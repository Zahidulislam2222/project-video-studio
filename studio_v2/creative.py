"""Narration-bound visual beats and reusable reference palettes, without invented facts."""

import hashlib
import json
from typing import cast

from PIL import Image, ImageOps

from .models import Beat, Theme


def spoken_beats(settings, shot, cues):
    if shot.beats or not shot.automatic_beats or not cues:
        return shot
    hold = settings.config["render"]["beat_hold_seconds"]
    beats: list[Beat] = []
    for cue in cues:
        if beats and cue["start"] - beats[-1].start < hold:
            continue
        text = cue["text"]
        beats.append(Beat(start=cue["start"], title=text[:110], labels=shot.labels))
        if len(beats) == 60:
            break
    return shot.model_copy(update={"beats": beats})


def train_profile(settings, references, output, notes):
    if not 1 <= len(references) <= settings.config["reference"]["maximum_images"]:
        raise ValueError("Supply a bounded set of consistent style images")
    output.mkdir(parents=True, exist_ok=False)
    swatches, sources = [], []
    for path in references:
        if path.stat().st_size > settings.config["storage"]["upload_bytes"]:
            raise ValueError("Reference exceeds the configured input limit")
        with Image.open(path) as original:
            if original.width * original.height > settings.config["reference"]["maximum_pixels"]:
                raise ValueError("Reference image exceeds the configured pixel limit")
            image = ImageOps.exif_transpose(original).convert("RGB")
            image.thumbnail((256, 256))
            indexed = image.quantize(colors=settings.config["reference"]["palette_colors"]).convert(
                "RGB"
            )
            swatches.extend(
                cast(list[tuple[int, tuple[int, int, int]]], indexed.getcolors(65536) or [])
            )
        sources.append({"name": path.name, "sha256": hashlib.sha256(path.read_bytes()).hexdigest()})
    swatches.sort(reverse=True)
    colors = [rgb for _, rgb in swatches]

    def luminance(rgb):
        values = [c / 255 for c in rgb]
        linear = [v / 12.92 if v <= 0.04045 else ((v + 0.055) / 1.055) ** 2.4 for v in values]
        return sum(c * w for c, w in zip(linear, (0.2126, 0.7152, 0.0722), strict=True))

    def contrast(a, b):
        a, b = sorted((luminance(a), luminance(b)))
        return (b + 0.05) / (a + 0.05)

    background = colors[0]
    foreground = max(
        [(255, 255, 255), (15, 15, 15), *colors], key=lambda c: contrast(c, background)
    )
    accent = max(colors, key=lambda c: contrast(c, background))
    if contrast(accent, background) < 3:
        accent = foreground
    panel = tuple(round(a * 0.88 + b * 0.12) for a, b in zip(background, foreground, strict=True))
    hexes = ["#{:02x}{:02x}{:02x}".format(*c) for c in (background, foreground, accent, panel)]
    theme = Theme(**dict(zip(("background", "foreground", "accent", "panel"), hexes, strict=True)))
    profile = {
        "theme": theme.model_dump(),
        "notes": notes,
        "sources": sources,
        "text_contrast": round(contrast(background, foreground), 2),
        "scope": "Palette extraction plus operator art-direction notes. Typography, texture, camera and motion need style/animation review.",
    }
    (output / "StyleProfile.json").write_text(json.dumps(profile, indent=2))
    width = settings.config["reference"]["swatch_width"]
    sheet = Image.new("RGB", (width * 4, width))
    for i, color in enumerate(hexes):
        sheet.paste(color, (i * width, 0, (i + 1) * width, width))
    sheet.save(output / "Palette.png")
    return profile
