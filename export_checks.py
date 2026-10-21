"""Source provenance and measured audio checks for new flexible-film exports."""

from __future__ import annotations

import hashlib
import json
import re
import wave
from dataclasses import replace
from pathlib import Path
from typing import Any

from asset_library import validate_record
from config import Film, Settings, contained, read_json
from media_tools import ffmpeg


def record_sources(film: Film, output: Path) -> None:
    sources = []
    for scene in film.scenes:
        if scene.media:
            sources.append(
                {
                    "scene": scene.ident,
                    "path": str(scene.media.relative_to(film.folder)),
                    "sha256": hashlib.sha256(scene.media.read_bytes()).hexdigest(),
                    "purpose": "illustration" if scene.illustrative else "owner-supplied media",
                }
            )
    if film.sound_enabled and film.ambience:
        sources.append(
            {
                "scene": "ambience",
                "path": str(film.ambience.relative_to(film.folder)),
                "sha256": hashlib.sha256(film.ambience.read_bytes()).hexdigest(),
                "purpose": "confirmed non-musical ambience",
            }
        )
    (output / "SourceInputs.json").write_text(
        json.dumps(sources, indent=2) + "\n", encoding="utf-8"
    )


def verify_sources(settings: Settings, output: Path, recorded: dict[str, Any]) -> dict[str, Any]:
    sources = json.loads((output / "SourceInputs.json").read_text(encoding="utf-8"))
    project = output.parents[1]
    for item in sources:
        path = contained(project, item["path"])
        if not path.is_file() or hashlib.sha256(path.read_bytes()).hexdigest() != item["sha256"]:
            raise ValueError("Original media changed during or after rendering: " + item["scene"])
    online = json.loads((output / "AssetSources.json").read_text(encoding="utf-8"))
    effective = replace(settings, data=recorded)
    for item in online:
        if "fallback" in item:
            continue
        validate_record(effective, item["request"], item)
        if not any(x["scene"] == item["scene"] and x["sha256"] == item["sha256"] for x in sources):
            raise ValueError("Online attribution is not bound to the rendered source")
    return {
        "hashes": "passed",
        "inputs": len(sources),
        "online_records": len(online),
        "limits": "Source identity and recorded license checked; relevance/rights require editorial review.",
    }


def measured_audio(settings: Settings, output: Path, path: Path) -> dict[str, float]:
    log = ffmpeg(
        settings, ["-i", path, "-vn", "-af", "ebur128=peak=true", "-f", "null", "-"], output
    )
    loudness = re.findall(r"I:\s*(-?[\d.]+) LUFS", log)
    peaks = re.findall(r"Peak:\s*(-?[\d.]+) dBFS", log)
    if not loudness or not peaks:
        raise ValueError("Could not measure final audio")
    return {"integrated_lufs": float(loudness[-1]), "true_peak_dbfs": float(peaks[-1])}


def verify_audio(
    settings: Settings, output: Path, recorded: dict[str, Any], duration: float
) -> dict[str, Any]:
    limits = recorded["verification"]
    stems = {}
    film_input = read_json(output / "film-input.json")
    enabled = film_input.get("sound", {}).get("enabled", False)
    names = (
        ("Voiceover.wav", "SoundEffects.wav", "Soundtrack.wav") if enabled else ("Voiceover.wav",)
    )
    for name in names:
        path = output / name
        with wave.open(str(path), "rb") as audio:
            seconds = audio.getnframes() / audio.getframerate()
            if (
                audio.getnchannels() != 2
                or audio.getframerate() != recorded["render"]["audio_rate"]
                or abs(seconds - duration) > limits["stem_duration_tolerance_seconds"]
            ):
                raise ValueError("Audio stem duration or format mismatch: " + name)
        stems[name] = {"seconds": seconds, "sha256": hashlib.sha256(path.read_bytes()).hexdigest()}
    if enabled:
        sound = read_json(output / "SoundDesign.json")
        if sound["music"] is not False or not sound["ducking"]:
            raise ValueError("Non-music/voice-ducking sound policy missing")
    levels = measured_audio(settings, output, output / "Film-Clean.mp4")
    if (
        abs(levels["integrated_lufs"] - recorded["render"]["loudness"])
        > limits["loudness_tolerance_lu"]
        or levels["true_peak_dbfs"] > limits["peak_ceiling_dbfs"]
    ):
        raise ValueError("Final audio outside configured loudness/peak limits")
    return {
        "levels": levels,
        "stems": stems,
        "music": False,
        "limits": "Measured levels and stem integrity do not replace human listening.",
    }
