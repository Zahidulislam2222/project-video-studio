"""Local recurrent human matting with immutable sources and synchronized masks."""

import asyncio
import json
import math
import os
import shutil
import sys
from pathlib import Path

from pydantic import Field

from .models import Contract
from .process import probe, python_environment, render_lock, run, stream_duration
from .render import digest


class MatteRequest(Contract):
    start: float = Field(ge=0)
    seconds: float = Field(gt=0)


def model_path(settings):
    value = os.environ.get("STUDIO_MATTING_MODEL", "")
    source = Path(value).resolve() if value else None
    if not source or not source.is_file():
        raise ValueError("Configure the local human matting model before requesting cutouts")
    if digest(source) != settings.config["matting"]["model_sha256"]:
        raise ValueError("Human matting model integrity check failed")
    return source


async def matte(settings, source, output, start, seconds):
    settings.data.mkdir(parents=True, exist_ok=True)
    with render_lock(settings):
        async with asyncio.timeout(settings.config["matting"]["timeout_seconds"]):
            return await _matte(settings, source, output, start, seconds)


async def _matte(settings, source, output, start, seconds):
    request = MatteRequest(start=start, seconds=seconds)
    cfg = settings.config["matting"]
    if request.seconds > cfg["maximum_seconds"]:
        raise ValueError("Split presenter footage into shorter shots before human matting")
    if output.exists():
        raise ValueError("Choose a new cutout folder; earlier results are preserved")
    if not settings.ffmpeg or not settings.ffprobe:
        raise ValueError("Human matting requires FFmpeg and ffprobe")
    model = model_path(settings)
    source = source.resolve(strict=True)
    if source.stat().st_size > settings.config["storage"]["upload_bytes"]:
        raise ValueError("Presenter footage exceeds the configured input limit")
    output.mkdir(parents=True)
    info = await probe(settings, source, output)
    video = next((s for s in info["streams"] if s["codec_type"] == "video"), None)
    if video is None:
        raise ValueError("Human matting requires a video stream")
    available = stream_duration(info, "video")
    if (
        request.start >= available
        or request.start + request.seconds > available + cfg["timing_tolerance"]
    ):
        raise ValueError("Presenter footage does not cover the requested shot")
    fps = settings.config["render"]["fps"]
    count = math.ceil(request.seconds * fps)
    width, height = int(video["width"]), int(video["height"])
    if not width or not height or width * height > cfg["maximum_source_pixels"]:
        raise ValueError("Presenter source dimensions exceed the configured pixel limit")
    # FFmpeg autorotates phone footage. Conservative square budgeting also covers rotation.
    edge = cfg["maximum_edge"]
    working_bytes = count * min(max(width, height), edge) ** 2 * cfg["working_bytes_per_pixel"]
    if working_bytes > cfg["maximum_working_bytes"]:
        raise ValueError(
            "Human matting exceeds the configured working-space limit; shorten this shot"
        )
    if shutil.disk_usage(output).free < working_bytes + cfg["free_disk_reserve_bytes"]:
        raise ValueError("Insufficient free disk for bounded human matting")
    source_hash = digest(source)
    frames = output / "frames"
    frames.mkdir()
    await run(
        [
            settings.ffmpeg,
            "-hide_banner",
            "-n",
            "-threads",
            str(cfg["threads"]),
            "-protocol_whitelist",
            "file,pipe",
            "-ss",
            str(request.start),
            "-i",
            str(source),
            "-an",
            "-vf",
            f"scale=w='min(iw,{edge})':h='min(ih,{edge})':force_original_aspect_ratio=decrease:force_divisible_by=2,setsar=1,fps={fps},tpad=stop_mode=clone:stop_duration={cfg['timing_tolerance']}",
            "-frames:v",
            str(count),
            "-threads",
            str(cfg["threads"]),
            str(frames / "src-%06d.png"),
        ],
        output,
        cfg["timeout_seconds"],
    )
    if len(list(frames.glob("src-*.png"))) != count:
        raise ValueError("Decoded presenter frame count does not cover the shot")
    (output / "MatteRequest.json").write_text(
        json.dumps(
            {
                "frames": count,
                "model": str(model),
                "source_sha256": source_hash,
                "start": request.start,
                "seconds": request.seconds,
                "fps": fps,
            },
            indent=2,
        )
    )
    await run(
        [sys.executable, "-m", "studio_v2.matting_worker", str(output)],
        output,
        cfg["timeout_seconds"],
        env=python_environment(settings),
    )
    inference = json.loads((output / "MatteInference.json").read_text())
    for prefix, name, pixel_format in (
        ("foreground", "Foreground.mkv", "bgr0"),
        ("mask", "Mask.mkv", "gray"),
    ):
        await run(
            [
                settings.ffmpeg,
                "-hide_banner",
                "-n",
                "-threads",
                str(cfg["threads"]),
                "-framerate",
                str(fps),
                "-i",
                str(frames / (prefix + "-%06d.png")),
                "-frames:v",
                str(count),
                "-an",
                "-c:v",
                "ffv1",
                "-level",
                "3",
                "-threads",
                str(cfg["threads"]),
                "-pix_fmt",
                pixel_format,
                str(output / name),
            ],
            output,
            cfg["timeout_seconds"],
        )
        if (output / name).stat().st_size > settings.config["storage"]["derived_asset_bytes"]:
            raise ValueError("Generated cutout exceeds the derived-media size limit; shorten this shot")
        await run(
            [
                settings.ffmpeg,
                "-v",
                "error",
                "-xerror",
                "-i",
                str(output / name),
                "-map",
                "0:v:0",
                "-f",
                "null",
                "-",
            ],
            output,
            cfg["timeout_seconds"],
        )
        measured = json.loads(
            await run(
                [
                    settings.ffprobe,
                    "-v",
                    "error",
                    "-count_frames",
                    "-select_streams",
                    "v:0",
                    "-show_entries",
                    "stream=nb_read_frames,width,height",
                    "-of",
                    "json",
                    str(output / name),
                ],
                output,
                cfg["timeout_seconds"],
            )
        )["streams"][0]
        if [measured["width"], measured["height"]] != inference["dimensions"]:
            raise ValueError("Foreground and alpha mask dimensions do not match")
        if int(measured["nb_read_frames"]) != count:
            raise ValueError("Encoded foreground or mask frame count mismatch")
    if digest(source) != source_hash:
        raise ValueError("Presenter source changed during processing")
    result = inference
    result.update(
        {
            "source_sha256": source_hash,
            "start": request.start,
            "seconds": count / fps,
            "fps": fps,
            "frames": count,
            "foreground": {
                "file": "Foreground.mkv",
                "sha256": digest(output / "Foreground.mkv"),
            },
            "mask": {"file": "Mask.mkv", "sha256": digest(output / "Mask.mkv")},
            "full_decode": True,
            "dimensions": [measured["width"], measured["height"]],
            "limits": cfg["limitations"],
        }
    )
    (output / "MatteVerification.json").write_text(json.dumps(result, indent=2))
    # Only successful generated intermediates in this exclusive output folder are reclaimed.
    # Failed-run intermediates remain available for diagnosis.
    if not cfg["retain_frames"]:
        shutil.rmtree(frames)
    return result
