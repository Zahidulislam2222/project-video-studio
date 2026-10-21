"""Write a Final Cut Pro 7 XML timeline with local media references."""

from __future__ import annotations

from pathlib import Path
from typing import Any

from defusedxml import ElementTree as XML

from media_tools import tool_path


def node(parent: Any, tag: str, value: Any = None, **attributes: Any) -> Any:
    item = XML.fromstring("<" + tag + "/>")
    for k, v in attributes.items():
        item.set(k, str(v))
    if value is not None:
        item.text = str(value)
    if parent is not None:
        parent.append(item)
    return item


def rate(parent: Any, fps: int) -> None:
    item = node(parent, "rate")
    node(item, "timebase", fps)
    node(item, "ntsc", "FALSE")


def location(path: Path) -> str:
    # Windows editors need Windows file URIs even when the authoring CLI uses WSL.
    if str(path.resolve()).startswith("/mnt/"):
        from urllib.parse import quote

        return "file://localhost/" + quote(tool_path(path, True), safe=":/")
    return path.resolve().as_uri()


def write_timeline(folder: Path, story: dict[str, Any]) -> None:
    root = node(None, "xmeml", version="5")
    seq = node(root, "sequence", id="project-film")
    node(seq, "name", story["title"])
    total = sum(s["frames"] for s in story["scenes"])
    node(seq, "duration", total)
    rate(seq, story["fps"])
    media = node(seq, "media")
    video = node(media, "video")
    fmt = node(node(video, "format"), "samplecharacteristics")
    rate(fmt, story["fps"])
    for k, v in (
        ("width", story["width"]),
        ("height", story["height"]),
        ("anamorphic", "FALSE"),
        ("pixelaspectratio", "square"),
        ("fielddominance", "none"),
    ):
        node(fmt, k, v)
    track, cursor = node(video, "track"), 0
    for index, scene in enumerate(story["scenes"]):
        path = folder / "media" / (scene["id"] + ".mp4")
        if not path.is_file():
            raise ValueError("Timeline media missing")
        clip = node(track, "clipitem", id="clip" + str(index))
        for k, v in (
            ("name", path.name),
            ("duration", scene["frames"]),
            ("start", cursor),
            ("end", cursor + scene["frames"]),
            ("in", 0),
            ("out", scene["frames"]),
            ("enabled", "TRUE"),
        ):
            node(clip, k, v)
        rate(clip, story["fps"])
        file = node(clip, "file", id="file" + str(index))
        node(file, "name", path.name)
        node(file, "pathurl", location(path))
        node(file, "duration", scene["frames"])
        rate(file, story["fps"])
        vf = node(node(node(file, "media"), "video"), "samplecharacteristics")
        for k, v in (
            ("width", story["width"]),
            ("height", story["height"]),
            ("pixelaspectratio", "square"),
        ):
            node(vf, k, v)
        rate(vf, story["fps"])
        cursor += scene["frames"]
    audio = node(media, "audio")
    node(audio, "numOutputChannels", 2)
    soundtrack = "Soundtrack.wav" if (folder / "Soundtrack.wav").is_file() else "Voiceover.wav"
    for channel in (1, 2):
        clip = node(node(audio, "track"), "clipitem", id="voice" + str(channel))
        for k, v in (
            ("name", soundtrack),
            ("duration", total),
            ("start", 0),
            ("end", total),
            ("in", 0),
            ("out", total),
            ("enabled", "TRUE"),
        ):
            node(clip, k, v)
        rate(clip, story["fps"])
        file = node(clip, "file", id="voice-file")
        if channel == 1:
            node(file, "name", soundtrack)
            node(file, "pathurl", location(folder / soundtrack))
            rate(file, story["fps"])
            node(file, "duration", total)
            af = node(node(file, "media"), "audio")
            node(af, "channelcount", 2)
            sample = node(af, "samplecharacteristics")
            node(sample, "samplerate", story["audio_rate"])
            node(sample, "depth", 16)
        source = node(clip, "sourcetrack")
        node(source, "mediatype", "audio")
        node(source, "trackindex", channel)
    (folder / "Timeline.xml").write_bytes(
        XML.tostring(root, encoding="utf-8", xml_declaration=True)
    )
