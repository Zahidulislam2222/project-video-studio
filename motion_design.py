"""Data-driven, frame-aligned motion primitives for the existing FFmpeg engine."""

from __future__ import annotations

from typing import Any

from config import Scene, Settings


def ease(progress: str) -> str:
    # Cubic ease-out is a mathematical invariant, not a delivery default.
    return f"(1-pow(1-clip({progress},0,1),3))"


def title_motion(settings: Settings, scene: Scene, y: int, subtitle: bool = False) -> str:
    p = settings.data["motion_presets"][scene.motion]
    if not p["enabled"]:
        return f":x={settings.data['render']['title_x']}:y={y}"
    delay = p["stagger_seconds"] if subtitle else 0
    progress = f"(t-{delay})/{p['reveal_seconds']}"
    eased = ease(progress)
    return (
        f":x={settings.data['render']['title_x']}"
        f":y='{y}+{p['slide_pixels']}*(1-{eased})'"
        f":alpha='clip({progress},0,1)'"
    )


def picture_motion(settings: Settings, scene: Scene, timing: dict[str, Any]) -> str:
    p, r = settings.data["motion_presets"][scene.motion], settings.data["render"]
    if (
        not p["enabled"]
        or not scene.media
        or scene.media.suffix.lower() not in (".png", ".jpg", ".jpeg")
    ):
        return ""
    # Animate only still images. Screen recordings stay uncropped and legible.
    frames = max(1, timing["frames"] - 1)
    zoom = f"1+({p['image_zoom']}-1)*on/{frames}"
    return (
        f",zoompan=z='{zoom}':x='(iw-iw/zoom)*(0.5+{p['pan_fraction']}*on/{frames})'"
        f":y='(ih-ih/zoom)/2':d=1:s={r['width']}x{r['height']}:fps={r['fps']}"
    )


def accent_motion(settings: Settings, scene: Scene, y: int) -> str:
    p, r = settings.data["motion_presets"][scene.motion], settings.data["render"]
    if not p["enabled"] or not p["accent_fraction"]:
        return ""
    # drawtext's box uses per-frame text positioning; a bar grows into view.
    return (
        f",drawtext=fontfile=regular.ttf:text=' ':expansion=none:fontsize=1"
        f":fontcolor={r['accent']}:box=1:boxcolor={r['accent']}"
        f":boxw={round(r['width'] * p['accent_fraction'])}:boxh={p['accent_thickness']}"
        f":x='{r['title_x']}-({round(r['width'] * p['accent_fraction'])})"
        f"*(1-{ease('t/' + str(p['reveal_seconds']))})':y={y}"
    )


def scene_fade(settings: Settings, scene: Scene, duration: float) -> str:
    p = settings.data["motion_presets"][scene.motion]
    fade = p["fade_seconds"] if p["enabled"] else settings.data["render"]["fade"]
    if not fade:
        return ""
    fade = min(fade, duration / 2)
    return f",fade=t=in:st=0:d={fade},fade=t=out:st={duration - fade}:d={fade}"
