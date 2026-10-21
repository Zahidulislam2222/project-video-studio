"""Measured reference breakdown; no source footage is reused in generated films."""

import json
import math
import re
from pathlib import Path
from typing import cast

from PIL import Image, ImageDraw

from .process import probe, run
from .render import digest


async def analyze(settings, source: Path, folder: Path):
    if not source.is_file():
        raise ValueError("Reference video not found")
    folder.mkdir(parents=True, exist_ok=False)
    info = await probe(settings, source, folder)
    video = next((s for s in info["streams"] if s["codec_type"] == "video"), None)
    if video is None:
        raise ValueError("Reference has no video stream")
    duration = float(info["format"]["duration"])
    cfg = settings.config["reference"]
    count = min(cfg["frames"], max(1, math.floor(duration)))
    await run(
        [
            settings.ffmpeg,
            "-hide_banner",
            "-n",
            "-protocol_whitelist",
            "file,pipe",
            "-i",
            str(source),
            "-an",
            "-vf",
            f"fps={count / duration},scale=480:-2",
            "-frames:v",
            str(count),
            "frame-%03d.jpg",
        ],
        folder,
        settings.config["render"]["timeout_seconds"],
    )
    await run(
        [
            settings.ffmpeg,
            "-hide_banner",
            "-n",
            "-protocol_whitelist",
            "file,pipe",
            "-i",
            str(source),
            "-an",
            "-vf",
            f"select='gt(scene,{cfg['cut_threshold']})',metadata=print:file=cuts.txt",
            "-fps_mode",
            "vfr",
            "-f",
            "null",
            "-",
        ],
        folder,
        settings.config["render"]["timeout_seconds"],
    )
    cuts = [float(t) for t in re.findall(r"pts_time:([0-9.]+)", (folder / "cuts.txt").read_text())]
    boundaries = [0, *[t for t in cuts if 0 < t < duration], duration]
    lengths = [b - a for a, b in zip(boundaries, boundaries[1:])]
    tiles = []
    colors: list[tuple[int, tuple[int, int, int]]] = []
    for i, path in enumerate(sorted(folder.glob("frame-*.jpg"))):
        with Image.open(path) as original:
            image = original.convert("RGB")
            image.thumbnail((320, 200))
            tile = Image.new("RGB", (340, 240), "#10141c")
            tile.paste(image, ((340 - image.width) // 2, 8))
            ImageDraw.Draw(tile).text(
                (10, 215),
                f"sample {i + 1} / approx {duration * (i + 0.5) / count:.1f}s",
                fill="white",
            )
            tiles.append(tile)
            sample_colors = (
                image.resize((100, 100))
                .quantize(colors=cfg["palette_colors"])
                .convert("RGB")
                .getcolors(10000)
            )
            colors.extend(cast(list[tuple[int, tuple[int, int, int]]], sample_colors or []))
    sheet = Image.new("RGB", (340 * 4, 240 * math.ceil(len(tiles) / 4)), "#10141c")
    for i, tile in enumerate(tiles):
        sheet.paste(tile, ((i % 4) * 340, (i // 4) * 240))
    sheet.save(folder / "contact-sheet.jpg")
    totals: dict[tuple[int, int, int], int] = {}
    for n, color in colors:
        totals[color] = totals.get(color, 0) + n
    palette = [
        f"#{color[0]:02x}{color[1]:02x}{color[2]:02x}"
        for color in sorted(totals, key=lambda c: totals[c], reverse=True)[: cfg["palette_colors"]]
    ]
    result = {
        "source_sha256": digest(source),
        "duration": duration,
        "dimensions": [video["width"], video["height"]],
        "cuts": cuts,
        "shot_lengths": lengths,
        "average_shot_seconds": sum(lengths) / len(lengths),
        "palette": palette,
        "framing": "portrait" if video["height"] > video["width"] else "landscape",
        "limits": [
            "Scene detection can miss dissolves and camera movement",
            "Palette is estimated from sampled frames",
            "Typography, transitions, camera movement and audio beat need visual/listening review",
            "Reference assets are excluded from exports",
        ],
    }
    (folder / "analysis.json").write_text(json.dumps(result, indent=2))
    return result
