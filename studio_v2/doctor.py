"""Read actual local prerequisites; configuration presence is not an integration test."""

import json
import os
import uuid
from pathlib import Path

from .process import run
from .render import digest


async def doctor(settings):
    result = {
        "tools": {},
        "font": settings.font.is_file(),
        "offline_voice": "unconfigured",
        "optional": {},
    }
    folder = settings.contained("checks", uuid.uuid4().hex)
    for name, binary in [("ffmpeg", settings.ffmpeg), ("ffprobe", settings.ffprobe)]:
        if not binary or not Path(binary).is_file():
            raise ValueError("Configure the installed " + name + " executable")
        output = await run(
            [binary, "-version"], folder, settings.config["render"]["shutdown_seconds"]
        )
        result["tools"][name] = output.decode(errors="replace").splitlines()[0]
    if not settings.font.is_file():
        raise ValueError("Configured font is unavailable")
    if settings.model and settings.voices:
        legacy = json.loads((settings.root / "settings.json").read_text())
        for key, path in [("model", settings.model), ("voices", settings.voices)]:
            if not path.is_file() or digest(path) != legacy[key + "_sha256"]:
                raise ValueError("Offline narration asset integrity check failed")
        result["offline_voice"] = "hashes_verified"
    result["optional"] = {
        "blender": "configured; verify by rendering"
        if Path(os.environ.get("STUDIO_BLENDER", "")).is_file()
        else "unconfigured",
        "transcription": "configured; verify by transcribing"
        if Path(os.environ.get("STUDIO_TRANSCRIPTION_MODEL", "")).is_dir()
        and os.environ.get("STUDIO_TRANSCRIPTION_MODEL")
        else "unconfigured",
        "director": "configured; verify with a local storyboard request"
        if os.environ.get("STUDIO_AI_URL") and os.environ.get("STUDIO_AI_MODEL")
        else "unconfigured",
    }
    if os.environ.get("STUDIO_MATTING_MODEL"):
        from .matting import model_path

        model_path(settings)
        result["optional"]["human_matting"] = (
            "Model hash verified; verify edge quality with footage previews"
        )
    else:
        result["optional"]["human_matting"] = "unconfigured"
    result["scope"] = (
        "Local prerequisites and narration asset hashes. Optional tools require their own real-flow checks."
    )
    return result
