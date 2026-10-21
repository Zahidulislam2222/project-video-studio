"""Explicit local editor and capture adapters; nothing installs or publishes silently."""

import json
import os
from pathlib import Path

from .process import native_args, run


async def blender(settings, output: Path, labels: list[str], seconds: float, transparent=False):
    binary = os.environ.get("STUDIO_BLENDER")
    if not binary or not Path(binary).is_file():
        raise ValueError("Configure the installed Blender executable")
    if (
        not 1 <= seconds <= 60
        or not 2 <= len(labels) <= 5
        or any(not label or len(label) > 30 for label in labels)
    ):
        raise ValueError("Use 2–5 short labels and a 1–60 second shot")
    output.mkdir(parents=True, exist_ok=False)
    cfg = settings.config["blender"]
    native_output = native_args([binary, str(output)])[1]
    spec = {
        "labels": labels,
        "width": cfg["width"],
        "height": cfg["height"],
        "fps": cfg["fps"],
        "frames": round(seconds * cfg["fps"]),
        "output": native_output,
        "transparent": transparent,
    }
    (output / "SceneRequest.json").write_text(json.dumps(spec))
    codec = (
        ["-c:v", "prores_ks", "-profile:v", "4", "-pix_fmt", "yuva444p10le", "Shot.mov"]
        if transparent
        else ["-c:v", "libx264", "-pix_fmt", "yuv420p", "Shot.mp4"]
    )
    await run(
        [
            binary,
            "--background",
            "--factory-startup",
            "--python-exit-code",
            "1",
            "--python",
            str(settings.root / "studio_v2/blender_scene.py"),
            "--",
            str(output / "SceneRequest.json"),
        ],
        output,
        cfg["timeout_seconds"],
    )
    await run(
        [
            settings.ffmpeg,
            "-hide_banner",
            "-n",
            "-framerate",
            str(cfg["fps"]),
            "-i",
            "frame-%04d.png",
            *codec,
        ],
        output,
        settings.config["render"]["timeout_seconds"],
    )
    return output / ("Shot.mov" if transparent else "Shot.mp4")
