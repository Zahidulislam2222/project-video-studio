"""One validated configuration boundary for the local video workspace."""

from __future__ import annotations

import json
import math
import re
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any
from urllib.parse import urlsplit


def read_json(path: Path) -> dict[str, Any]:
    result = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(result, dict):
        raise TypeError("Configuration must be a JSON object")
    return result


def contained(root: Path, name: str) -> Path:
    candidate = (root / name).resolve()
    if not candidate.is_relative_to(root.resolve()) or candidate == root.resolve():
        raise ValueError("Path must stay inside its owning folder")
    return candidate


def slug(value: str) -> str:
    if not re.fullmatch(r"[a-z0-9]+(?:-[a-z0-9]+)*", value):
        raise ValueError("Use lowercase letters, numbers and single hyphens for names")
    return value


def number(value: Any, minimum: float, maximum: float) -> float:
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        raise TypeError("Expected a number")
    if not math.isfinite(value) or not minimum <= value <= maximum:
        raise ValueError("Number outside supported range")
    return float(value)


def safe_text(value: Any) -> str:
    if not isinstance(value, str) or not value.strip():
        raise ValueError("Text must be nonempty")
    if any(ord(c) < 32 and c not in "\n\t" for c in value):
        raise ValueError("Control characters are not allowed")
    # ASS override syntax is never interpreted from project content.
    if any(c in value for c in "{}\\"):
        raise ValueError("Caption control syntax is not allowed in content")
    return value.strip()


def boolean(value: Any) -> bool:
    if not isinstance(value, bool):
        raise TypeError("Expected true or false")
    return value


def output_settings(render: dict[str, Any], captions: dict[str, Any]) -> None:
    for key in ("width", "height", "fps", "audio_rate"):
        value = render[key]
        if isinstance(value, bool) or not isinstance(value, int) or value <= 0:
            raise ValueError("Render dimensions and rates must be positive integers")
    if render["width"] % 2 or render["height"] % 2:
        raise ValueError("H264 output needs even dimensions")
    for key in ("background", "accent", "foreground"):
        if not re.fullmatch(r"0x[0-9a-fA-F]{6}", render[key]):
            raise ValueError("Colors must be hexadecimal RGB")
    for key in ("title_size", "subtitle_size", "title_gap", "header_height"):
        number(render[key], 1, render["height"])
    for key in ("title_x", "title_y"):
        number(render[key], 0, max(render["width"], render["height"]))
    for key in ("header_opacity", "card_title_y_fraction", "fade", "scene_lead", "scene_tail"):
        number(render[key], 0, 1)
    number(render["crf"], 0, 51)
    if render["preset"] not in (
        "ultrafast",
        "superfast",
        "veryfast",
        "faster",
        "fast",
        "medium",
        "slow",
        "slower",
        "veryslow",
    ):
        raise ValueError("Unsupported H264 encoding preset")
    if not re.fullmatch(r"[a-zA-Z0-9 ]+", captions["font"]):
        raise ValueError("Invalid subtitle font name")
    if captions["lines"] != 2 or captions["line_characters"] < 12:
        raise ValueError("Use two readable caption lines")
    for key in ("size", "margin_horizontal", "margin_vertical", "safe_band"):
        number(captions[key], 1, max(render["width"], render["height"]))
    number(captions["band_opacity"], 0, 1)
    number(captions["minimum_seconds"], 0.1, 10)


def sound_settings(audio: dict[str, Any]) -> None:
    for key in ("effects_gain_db", "ambience_gain_db"):
        number(audio[key], -60, -12)
    for key, low, high in (
        ("whoosh_seconds", 0.05, 1),
        ("click_seconds", 0.01, 0.2),
        ("fade_seconds", 0.01, 3),
        ("noise_smoothing", 1, 200),
        ("duck_threshold", 0.001, 1),
        ("duck_ratio", 1, 20),
        ("duck_attack_ms", 0.01, 2000),
        ("duck_release_ms", 0.01, 9000),
    ):
        number(audio[key], low, high)
    if (
        isinstance(audio["noise_seed"], bool)
        or not isinstance(audio["noise_seed"], int)
        or audio["noise_seed"] < 0
    ):
        raise ValueError("Noise seed must be a nonnegative integer")


def remote_request(raw: Any, settings: Settings, kind: str | None = None) -> dict[str, Any] | None:
    if raw is None:
        return None
    if not isinstance(raw, dict):
        raise TypeError("asset_request must be an object")
    result = dict(raw)
    if result.get("library") not in settings.data["asset_libraries"]:
        raise ValueError("Unknown asset library")
    if result.get("kind") not in ((kind,) if kind else ("image", "video")):
        raise ValueError("Unsupported asset request kind")
    result["query"] = safe_text(result["query"])
    if len(result["query"]) > settings.data["online"]["query_characters"]:
        raise ValueError("Asset query too long")
    if result.get("title") is not None:
        result["title"] = safe_text(result["title"])
    if result.get("fallback", "error") not in ("error", "card"):
        raise ValueError("Asset fallback must be error or card")
    if kind == "audio" and (
        result.get("non_musical_confirmed") is not True or not result.get("title")
    ):
        raise ValueError(
            "Online ambience needs a chosen file title and non_musical_confirmed: true"
        )
    return result


@dataclass(frozen=True)
class Delivery:
    speed: float
    sentence_pause: float
    clause_pause: float
    gap: float


@dataclass(frozen=True)
class Settings:
    root: Path
    data: dict[str, Any]
    machine: dict[str, Path]
    delivery: dict[str, Delivery]

    @classmethod
    def load(cls, root: Path) -> Settings:
        data = read_json(root / "settings.json")
        raw_machine = read_json(root / "machine.local.json")
        machine = {}
        for name in ("ffmpeg", "ffprobe", "font_regular", "font_bold"):
            path = Path(raw_machine[name])
            if not path.is_absolute() or not path.is_file():
                raise ValueError("Missing configured machine tool: " + name)
            machine[name] = path
        voices = data["male_voices"]
        if not voices or any(not re.fullmatch(r"[ab]m_[a-z]+", v) for v in voices):
            raise ValueError("Only documented English male voices are allowed")
        if any(lang not in ("en-us", "en-gb") for lang in voices.values()):
            raise ValueError("Unsupported narration language")
        if data["default_voice"] not in voices:
            raise ValueError("Default voice must be in male voice policy")
        limits = data["limits"]
        deliveries = {}
        for name, preset in data["delivery"].items():
            deliveries[name] = Delivery(
                number(preset["speed"], limits["speed_min"], limits["speed_max"]),
                number(preset["sentence_pause"], 0, 3),
                number(preset["clause_pause"], 0, 3),
                number(preset["gap"], 0, 3),
            )
        if data["default_delivery"] not in deliveries:
            raise ValueError("Unknown default delivery")
        for key in ("runtime_packages", "model", "voices"):
            contained(root, data[key])
        render, captions = data["render"], data["captions"]
        for key in ("width", "height", "fps", "audio_rate"):
            if not isinstance(render[key], int) or render[key] <= 0:
                raise ValueError("Render dimensions and rates must be positive integers")
        if render["width"] % 2 or render["height"] % 2:
            raise ValueError("H264 output needs even dimensions")
        for key in ("background", "accent", "foreground"):
            if not re.fullmatch(r"0x[0-9a-fA-F]{6}", render[key]):
                raise ValueError("Colors must be hexadecimal RGB")
        if not re.fullmatch(r"[a-zA-Z0-9 ]+", captions["font"]):
            raise ValueError("Invalid subtitle font name")
        if captions["lines"] != 2 or captions["line_characters"] < 12:
            raise ValueError("Use two readable caption lines")
        for name, preset in data["formats"].items():
            slug(name)
            minimum = number(preset["minimum_seconds"], 1, limits["max_duration_seconds"])
            number(preset["maximum_seconds"], minimum, limits["max_duration_seconds"])
            for key in ("intro_max_seconds", "outro_max_seconds"):
                number(preset[key], 1, preset["maximum_seconds"])
            for key in ("width", "height"):
                value = preset[key]
                if isinstance(value, bool) or not isinstance(value, int) or value < 2 or value % 2:
                    raise ValueError("Format dimensions must be positive even integers")
            if preset["motion"] not in data["motion_presets"]:
                raise ValueError("Unknown format motion preset")
            contained(root, preset["template"])
            if set(preset["render_overrides"]) - set(render) or set(
                preset["caption_overrides"]
            ) - set(captions):
                raise ValueError("Unknown output override")
            updated_render = {
                **render,
                **preset["render_overrides"],
                "width": preset["width"],
                "height": preset["height"],
            }
            output_settings(updated_render, {**captions, **preset["caption_overrides"]})
        output_settings(render, captions)
        if (
            data["default_format"] not in data["formats"]
            or data["default_asset_library"] not in data["asset_libraries"]
        ):
            raise ValueError("Unknown default format or asset library")
        for name, preset in data["motion_presets"].items():
            slug(name)
            for key, low, high in (
                ("reveal_seconds", 0.05, 3),
                ("stagger_seconds", 0, 2),
                ("slide_pixels", 0, 300),
                ("image_zoom", 1, 1.2),
                ("pan_fraction", 0, 1),
                ("accent_fraction", 0, 1),
                ("accent_thickness", 1, 20),
                ("fade_seconds", 0, 1),
            ):
                number(preset[key], low, high)
            boolean(preset["enabled"])
        sound_settings(data["sound"])
        number(data["planning"]["words_per_minute"], 60, 250)
        online = data["online"]
        boolean(online["enabled"])
        for key in ("timeout_seconds", "max_bytes", "max_results", "query_characters"):
            number(online[key], 1, 1_000_000_000)
        for library in data["asset_libraries"].values():
            endpoint = urlsplit(library["api_url"])
            if (
                library["cost"] != "free"
                or library["driver"] != "mediawiki"
                or endpoint.scheme != "https"
                or (
                    endpoint.hostname not in library["allowed_hosts"]
                    or endpoint.username
                    or endpoint.password
                    or endpoint.port not in (None, 443)
                )
            ):
                raise ValueError("Asset library requires a supported HTTPS public API")
        return cls(root.resolve(), data, machine, deliveries)


@dataclass(frozen=True)
class Scene:
    ident: str
    title: str
    subtitle: str
    media: Path | None
    trim_start: float
    delivery: str
    sentences: tuple[str, ...]
    role: str = "body"
    motion: str = "none"
    effect: str = "auto"
    asset_request: dict[str, Any] | None = None
    illustrative: bool = False


@dataclass(frozen=True)
class Film:
    folder: Path
    title: str
    author: str
    voice: str
    delivery: str
    pronunciation: dict[str, str]
    overlay_titles: bool
    scenes: tuple[Scene, ...]
    format_name: str = "custom"
    motion: str = "none"
    sound_enabled: bool = False
    ambience: Path | None = None
    ambience_request: dict[str, Any] | None = None
    sound_overrides: dict[str, Any] = field(default_factory=dict)

    @classmethod
    def load(cls, folder: Path, settings: Settings) -> Film:
        data = read_json(folder / "film.json")
        voice = data["voice"]
        if voice not in settings.data["male_voices"]:
            raise ValueError("Narration requires an approved male voice")
        delivery = data["delivery"]
        if delivery not in settings.delivery:
            raise ValueError("Unknown project delivery")
        if not isinstance(data["overlay_titles"], bool):
            raise TypeError("overlay_titles must be true or false")
        pronunciation = {safe_text(k): safe_text(v) for k, v in data["pronunciation"].items()}
        format_name = data.get("format", "custom")
        if format_name != "custom" and format_name not in settings.data["formats"]:
            raise ValueError("Unknown film format")
        motion = data.get("motion") or (
            settings.data["formats"][format_name]["motion"] if format_name != "custom" else "none"
        )
        if motion not in settings.data["motion_presets"]:
            raise ValueError("Unknown motion preset")
        sound = data.get("sound", {"enabled": False, "ambience": None})
        if set(sound) - {
            "enabled",
            "ambience",
            "non_musical_confirmed",
            "asset_request",
            "overrides",
        }:
            raise ValueError("Unknown sound field; put mix tuning in sound.overrides")
        sound_overrides = sound.get("overrides", {})
        if not isinstance(sound_overrides, dict) or set(sound_overrides) - set(
            settings.data["sound"]
        ):
            raise ValueError("Unknown sound override")
        sound_settings({**settings.data["sound"], **sound_overrides})
        sound_enabled = boolean(sound["enabled"])
        ambience_request = remote_request(sound.get("asset_request"), settings, "audio")
        ambience = contained(folder, sound["ambience"]) if sound.get("ambience") else None
        if sound_enabled and ambience and (not ambience.is_file() and not ambience_request):
            raise ValueError("Ambience file missing; provide an asset_request or a real file")
        if sound_enabled and ambience and sound.get("non_musical_confirmed") is not True:
            raise ValueError("Ambience must be confirmed non-musical")
        if (
            sound_enabled
            and ambience
            and ambience.suffix.lower() not in settings.data["asset_types"]["audio"].values()
        ):
            raise ValueError("Unsupported ambience file type")
        scenes, seen = [], set()
        if not 0 < len(data["scenes"]) <= settings.data["limits"]["max_scenes"]:
            raise ValueError("Invalid scene count")
        for raw in data["scenes"]:
            ident = slug(raw["id"])
            if ident in seen:
                raise ValueError("Scene IDs must be unique")
            seen.add(ident)
            request = remote_request(raw.get("asset_request"), settings)
            role = raw.get("role", "body")
            if role not in ("intro", "body", "proof", "outro"):
                raise ValueError("Unknown scene role")
            if role == "proof" and request:
                raise ValueError("Real project proof cannot be replaced with online stock")
            chosen_motion = raw.get("motion") or motion
            if chosen_motion not in settings.data["motion_presets"]:
                raise ValueError("Unknown scene motion preset")
            effect = raw.get("effect", "auto")
            if effect not in ("auto", "none", "whoosh", "click"):
                raise ValueError("Use only non-musical whoosh/click effects")
            media = contained(folder, raw["media"]) if raw["media"] else None
            if media and (
                (not media.is_file() and not request)
                or media.suffix.lower() not in (".mp4", ".webm", ".mov", ".png", ".jpg", ".jpeg")
            ):
                raise ValueError("Scene media missing or unsupported")
            chosen_delivery = raw["delivery"] or delivery
            if chosen_delivery not in settings.delivery:
                raise ValueError("Unknown scene delivery")
            sentences = tuple(safe_text(x) for x in raw["sentences"])
            if not sentences or any(
                len(x) > settings.data["limits"]["max_sentence_characters"] for x in sentences
            ):
                raise ValueError("Narration sentences missing or too long")
            scenes.append(
                Scene(
                    ident,
                    safe_text(raw["title"]),
                    safe_text(raw["subtitle"]),
                    media,
                    number(
                        raw["trim_start"],
                        0,
                        settings.data["limits"]["max_duration_seconds"],
                    ),
                    chosen_delivery,
                    sentences,
                    role,
                    chosen_motion,
                    effect,
                    request,
                )
            )
        if format_name != "custom" and (
            len(scenes) < 3
            or scenes[0].role != "intro"
            or scenes[-1].role != "outro"
            or any(s.role in ("intro", "outro") for s in scenes[1:-1])
        ):
            raise ValueError("Formatted films need one opening, body scenes and one ending")
        return cls(
            folder.resolve(),
            safe_text(data["title"]),
            safe_text(data["author"]),
            voice,
            delivery,
            pronunciation,
            data["overlay_titles"],
            tuple(scenes),
            format_name,
            motion,
            sound_enabled,
            ambience,
            ambience_request,
            sound_overrides,
        )


def film_settings(
    settings: Settings, format_name: str, sound_overrides: dict[str, Any] | None = None
) -> Settings:
    """Apply output format without mutating global defaults or legacy projects."""
    import copy
    from dataclasses import replace

    if format_name == "custom" and not sound_overrides:
        return settings
    data = copy.deepcopy(settings.data)
    if format_name != "custom":
        preset = data["formats"][format_name]
        data["render"].update(preset["render_overrides"])
        data["render"].update(width=preset["width"], height=preset["height"])
        data["captions"].update(preset["caption_overrides"])
    if sound_overrides:
        data["sound"].update(sound_overrides)
        sound_settings(data["sound"])
    return replace(settings, data=data)


def check_timing(settings: Settings, film: Film, timeline: list[dict[str, Any]]) -> dict[str, Any]:
    duration = sum(x["frames"] for x in timeline) / settings.data["render"]["fps"]
    report = {"format": film.format_name, "seconds": duration}
    if film.format_name == "custom":
        return report
    preset = settings.data["formats"][film.format_name]
    if not preset["minimum_seconds"] <= duration <= preset["maximum_seconds"]:
        raise ValueError(
            f"Actual film is {duration:.1f}s; {film.format_name} needs "
            f"{preset['minimum_seconds']}–{preset['maximum_seconds']}s. Revise the script."
        )
    for scene, timing in zip(film.scenes, timeline, strict=True):
        if (
            scene.role in ("intro", "outro")
            and timing["duration"] > preset[scene.role + "_max_seconds"]
        ):
            raise ValueError(f"{scene.role} exceeds its brief time budget; shorten that scene")
    report["range"] = [preset["minimum_seconds"], preset["maximum_seconds"]]
    return report
