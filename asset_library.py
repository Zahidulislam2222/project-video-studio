"""Free public media discovery, bounded HTTPS downloads and auditable provenance."""

from __future__ import annotations

import asyncio
import hashlib
import json
import uuid
from dataclasses import replace
from html.parser import HTMLParser
from pathlib import Path
from typing import Any
from urllib.parse import urlencode, urlsplit

import httpx

from config import Film, Settings, contained
from media_tools import ffmpeg, probe


class PlainText(HTMLParser):
    def __init__(self) -> None:
        super().__init__()
        self.parts: list[str] = []

    def handle_data(self, data: str) -> None:
        self.parts.append(data)


def plain(value: str) -> str:
    parser = PlainText()
    parser.feed(value)
    return " ".join(" ".join(parser.parts).split())


def public_url(library: dict[str, Any], url: str) -> Any:
    parsed = urlsplit(url)
    if (
        parsed.scheme != "https"
        or not parsed.hostname
        or parsed.hostname not in library["allowed_hosts"]
        or parsed.username
        or parsed.password
        or parsed.port not in (None, 443)
    ):
        raise ValueError("Asset URL outside the configured public HTTPS library")
    return parsed


def validate_record(settings: Settings, request: dict[str, Any], record: dict[str, Any]) -> None:
    library = settings.data["asset_libraries"][request["library"]]
    required = {"library", "kind", "mime", "suffix", "license", "creator", "title", "source", "url"}
    if not required.issubset(record):
        raise ValueError("Cached asset provenance is incomplete")
    if (
        record["library"] != request["library"]
        or record["kind"] != request["kind"]
        or record["license"] not in library["licenses"]
        or not record["creator"]
        or settings.data["asset_types"][request["kind"]].get(record["mime"]) != record["suffix"]
        or (request.get("title") and record["title"] != request["title"])
    ):
        raise ValueError("Cached asset no longer matches the current license/type/library policy")
    public_url(library, record["source"])
    public_url(library, record["url"])
    if request["kind"] == "audio" and request.get("non_musical_confirmed") is not True:
        raise ValueError("Cached ambience requires non-music confirmation")


def fetch(settings: Settings, library: dict[str, Any], url: str) -> bytes:
    """No cookies, credentials, redirects, arbitrary schemes or unbounded reads."""
    online = settings.data["online"]
    if not online["enabled"]:
        raise ValueError("Online discovery disabled; use cached or local assets")
    public_url(library, url)

    async def download() -> bytes:
        async with asyncio.timeout(online["timeout_seconds"]):
            async with httpx.AsyncClient(
                timeout=online["timeout_seconds"],
                follow_redirects=False,
                trust_env=False,
                verify=True,
            ) as client:
                async with client.stream(
                    "GET",
                    url,
                    headers={
                        "User-Agent": online["user_agent"],
                        "Accept-Encoding": "identity",
                    },
                ) as response:
                    if response.status_code != 200:
                        raise ValueError(
                            f"Asset library returned HTTP {response.status_code}; no redirect followed"
                        )
                    if response.headers.get("Content-Encoding", "identity").lower() not in (
                        "",
                        "identity",
                    ):
                        raise ValueError(
                            "Compressed transfer rejected to preserve bounded asset reads"
                        )
                    size = response.headers.get("Content-Length")
                    if size and int(size) > online["max_bytes"]:
                        raise ValueError("Asset exceeds configured download limit")
                    content = bytearray()
                    async for chunk in response.aiter_raw():
                        if len(content) + len(chunk) > online["max_bytes"]:
                            raise ValueError("Empty or oversized asset response")
                        content.extend(chunk)
                    if not content:
                        raise ValueError("Empty or oversized asset response")
                    return bytes(content)

    return asyncio.run(download())


class MediaWikiLibrary:
    """Adapter boundary: register another driver here for a genuinely different API."""

    def __init__(self, settings: Settings, name: str) -> None:
        self.settings = settings
        self.name = name
        self.library = settings.data["asset_libraries"][name]

    def search(self, request: dict[str, Any]) -> list[dict[str, Any]]:
        params: dict[str, Any] = {
            "action": "query",
            "format": "json",
            "prop": "imageinfo",
            "iiprop": "url|size|mime|extmetadata",
        }
        if request.get("title"):
            params["titles"] = request["title"]
        else:
            params.update(
                generator="search",
                gsrnamespace=6,
                gsrsearch=request["query"] + " " + self.library["search_filters"][request["kind"]],
                gsrlimit=self.settings.data["online"]["max_results"],
            )
        response = json.loads(
            fetch(self.settings, self.library, self.library["api_url"] + "?" + urlencode(params))
        )
        if "error" in response:
            raise ValueError("Public library query failed")
        candidates = []
        for page in sorted(
            response.get("query", {}).get("pages", {}).values(), key=lambda x: x.get("index", 0)
        ):
            if not page.get("imageinfo"):
                continue
            info = page["imageinfo"][0]
            meta = info.get("extmetadata", {})
            license_name = meta.get("LicenseShortName", {}).get("value", "")
            mime = info.get("mime")
            suffix = self.settings.data["asset_types"][request["kind"]].get(mime)
            if (
                not suffix
                or license_name not in self.library["licenses"]
                or info.get("size", 0) > self.settings.data["online"]["max_bytes"]
            ):
                continue
            creator = plain(meta.get("Artist", {}).get("value", ""))
            if not creator:
                continue
            description = plain(meta.get("ImageDescription", {}).get("value", ""))
            if request["kind"] == "audio" and any(
                word in (page["title"] + " " + description).lower()
                for word in self.settings.data["online"]["audio_excluded_terms"]
            ):
                continue
            candidates.append(
                {
                    "library": self.name,
                    "title": page["title"],
                    "url": info["url"],
                    "source": info["descriptionurl"],
                    "creator": creator,
                    "license": license_name,
                    "license_url": meta.get("LicenseUrl", {}).get("value", ""),
                    "description": description,
                    "mime": mime,
                    "suffix": suffix,
                    "kind": request["kind"],
                    "purpose": "illustration" if request["kind"] != "audio" else "ambience",
                    "non_musical_confirmed": request.get("non_musical_confirmed", False),
                }
            )
        return candidates


DRIVERS = {"mediawiki": MediaWikiLibrary}


def search(settings: Settings, request: dict[str, Any]) -> list[dict[str, Any]]:
    library = settings.data["asset_libraries"][request["library"]]
    return DRIVERS[library["driver"]](settings, request["library"]).search(request)


def acquire(settings: Settings, folder: Path, request: dict[str, Any]) -> dict[str, Any]:
    identity = hashlib.sha256(json.dumps(request, sort_keys=True).encode()).hexdigest()
    cache = contained(contained(folder, "assets"), "online")
    cache.mkdir(parents=True, exist_ok=True)
    record_path = contained(cache, identity + ".json")
    if record_path.is_file():
        record = json.loads(record_path.read_text(encoding="utf-8"))
        validate_record(settings, request, record)
        target = contained(folder, record["path"])
        if (
            target.is_file()
            and hashlib.sha256(target.read_bytes()).hexdigest() == record["sha256"]
            and record["request"] == request
        ):
            return record
        raise ValueError("Cached asset integrity failed; preserve and inspect it before reuse")
    candidates = search(settings, request)
    if not candidates:
        raise ValueError("No licensed asset matched; refine the query or supply local media")
    record = candidates[0]
    validate_record(settings, request, record)
    decoder = settings.data["asset_decoders"][record["mime"]]
    target = contained(cache, identity + record["suffix"])
    content = fetch(settings, settings.data["asset_libraries"][request["library"]], record["url"])
    temporary = contained(cache, identity + "-" + uuid.uuid4().hex + ".partial" + record["suffix"])
    with temporary.open("xb") as handle:
        handle.write(content)
    info = probe(settings, temporary, tuple(decoder["formats"]))
    expected = "audio" if request["kind"] == "audio" else "video"
    if not any(s["codec_type"] == expected for s in info["streams"]):
        raise ValueError("Downloaded media does not match the requested type")
    if not any(
        s.get("codec_name") in decoder["codecs"]
        for s in info["streams"]
        if s["codec_type"] == expected
    ):
        raise ValueError("Downloaded codec does not match its declared MIME type")
    # Probe metadata alone does not establish decodability.
    errors = ffmpeg(
        settings,
        [
            "-v",
            "error",
            "-protocol_whitelist",
            "file,pipe",
            "-format_whitelist",
            ",".join(decoder["formats"]),
            "-i",
            temporary,
            "-f",
            "null",
            "-",
        ],
        cache,
    )
    if errors.strip():
        raise ValueError("Downloaded media failed full decode")
    if target.exists():
        raise FileExistsError("Preserving an existing uncatalogued asset")
    temporary.rename(target)
    record.update(
        path=str(target.relative_to(folder)),
        sha256=hashlib.sha256(content).hexdigest(),
        request=request,
        modifications="Fitted to video frame; optional pan/zoom, fades and labels",
    )
    with record_path.open("x", encoding="utf-8") as handle:
        handle.write(json.dumps(record, indent=2, ensure_ascii=False) + "\n")
    return record


def request_for_cached_media(
    settings: Settings, folder: Path, path: Path | None
) -> dict[str, Any] | None:
    cache = contained(contained(folder, "assets"), "online")
    if path is None or not path.is_relative_to(cache):
        return None
    for sidecar in cache.glob("*.json"):
        record = json.loads(sidecar.read_text(encoding="utf-8"))
        if contained(folder, record["path"]) == path:
            from config import remote_request

            return remote_request(
                record["request"], settings, "audio" if record["kind"] == "audio" else None
            )
    raise ValueError(
        "Online cache media has no provenance; preserve it and restore its source record"
    )


def resolve(settings: Settings, film: Film, output: Path) -> Film:
    scenes, records = [], []
    for scene in film.scenes:
        cached_request = request_for_cached_media(settings, film.folder, scene.media)
        if cached_request and scene.asset_request and cached_request != scene.asset_request:
            raise ValueError("Asset request changed; clear media to acquire the new illustration")
        request = scene.asset_request or cached_request
        # An explicit request on a title card is also a request for online illustration.
        if cached_request or (request and (scene.media is None or not scene.media.is_file())):
            if scene.role == "proof":
                raise ValueError("Online stock cannot be used as real project proof")
            if request is None:
                raise ValueError("Online media request missing")
            try:
                record = acquire(settings, film.folder, request)
            except (OSError, ValueError, httpx.HTTPError) as error:
                if request.get("fallback", "error") != "card":
                    raise ValueError(f"Asset unavailable for {scene.ident}: {error}") from error
                records.append({"scene": scene.ident, "fallback": "card", "reason": str(error)})
                scene = replace(
                    scene, media=None, subtitle=settings.data["online"]["fallback_label"]
                )
            else:
                records.append({**record, "scene": scene.ident})
                scene = replace(
                    scene,
                    media=contained(film.folder, record["path"]),
                    subtitle=settings.data["online"]["stock_label"],
                    illustrative=True,
                )
        scenes.append(scene)
    ambience = film.ambience
    cached_ambience = (
        request_for_cached_media(settings, film.folder, ambience) if film.sound_enabled else None
    )
    if cached_ambience and film.ambience_request and cached_ambience != film.ambience_request:
        raise ValueError("Ambience request changed; clear ambience to acquire the new sound")
    ambience_request = film.ambience_request or cached_ambience
    if film.sound_enabled and (
        cached_ambience or (ambience_request and (ambience is None or not ambience.is_file()))
    ):
        if ambience_request is None:
            raise ValueError("Ambience request missing")
        record = acquire(settings, film.folder, ambience_request)
        records.append({**record, "scene": "ambience"})
        ambience = contained(film.folder, record["path"])
    (output / "AssetSources.json").write_text(
        json.dumps(records, indent=2, ensure_ascii=False) + "\n", encoding="utf-8"
    )
    lines = []
    for record in records:
        if "fallback" in record:
            lines.append(record["scene"] + ": illustration unavailable; explicit card fallback.")
        else:
            lines.append(
                f"{record['title']} — {record['creator']} — {record['license']}\n"
                f"Source: {record['source']}\nLicense: {record['license_url']}\n"
                f"Changes: {record['modifications']}\nSHA256: {record['sha256']}"
            )
    (output / "Attribution.txt").write_text("\n\n".join(lines) + "\n", encoding="utf-8")
    return replace(film, scenes=tuple(scenes), ambience=ambience)
