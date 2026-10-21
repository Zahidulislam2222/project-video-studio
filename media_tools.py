"""Safe argument-based access to FFmpeg and frame-aligned subtitle timing."""

from __future__ import annotations

import asyncio
import json
import textwrap
from pathlib import Path
from typing import Any

from config import Settings


def tool_path(path: Path, windows: bool) -> str:
    value = str(path.resolve())
    if windows:
        parts = path.resolve().parts
        if len(parts) < 4 or parts[1] != "mnt" or len(parts[2]) != 1:
            raise ValueError("Windows tools require media on a mounted Windows drive")
        value = parts[2].upper() + ":/" + "/".join(parts[3:])
    return value


def command(settings: Settings, tool: str, args: list[str | Path], cwd: Path) -> str:
    executable = settings.machine[tool]
    windows = executable.suffix.lower() == ".exe"
    converted = [tool_path(x, windows) if isinstance(x, Path) else x for x in args]

    async def execute() -> tuple[int, bytes, bytes]:
        child = await asyncio.create_subprocess_exec(
            str(executable),
            *converted,
            cwd=cwd,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
            stdin=asyncio.subprocess.DEVNULL,
        )
        try:
            stdout, stderr = await asyncio.wait_for(
                child.communicate(), timeout=settings.data["limits"]["command_timeout_seconds"]
            )
            return child.returncode or 0, stdout, stderr
        finally:
            if child.returncode is None:
                child.kill()
                await child.wait()

    code, stdout, stderr = asyncio.run(execute())
    if code:
        (cwd / (tool + "-failure.log")).write_text(
            stderr.decode("utf-8", errors="replace"), encoding="utf-8"
        )
        raise RuntimeError(tool + " failed; inspect the run's private failure log")
    return (stdout if tool == "ffprobe" else stderr).decode("utf-8", errors="replace")


def ffmpeg(settings: Settings, args: list[str | Path], cwd: Path) -> str:
    return command(settings, "ffmpeg", ["-hide_banner", "-n", *args], cwd)


def probe(settings: Settings, source: Path, formats: tuple[str, ...] = ()) -> dict[str, Any]:
    restrictions = ["-protocol_whitelist", "file,pipe"]
    if formats:
        restrictions += ["-format_whitelist", ",".join(formats)]
    return json.loads(
        command(
            settings,
            "ffprobe",
            ["-v", "error", *restrictions, "-show_streams", "-show_format", "-of", "json", source],
            source.parent,
        )
    )


def caption_chunks(text: str, width: int) -> list[str]:
    words = text.split()
    if any(len(w) > width for w in words):
        raise ValueError("A caption word is too long; revise its display text")
    lines = textwrap.wrap(
        " ".join(words), width=width, break_long_words=False, break_on_hyphens=False
    )
    chunks = ["\n".join(lines[i : i + 2]) for i in range(0, len(lines), 2)]
    if len(chunks) > 1 and len(chunks[-1].split()) < 3:
        together = (chunks[-2] + " " + chunks[-1]).split()
        choices = []
        for pivot in range(3, len(together) - 2):
            a, b = (" ".join(together[:pivot]), " ".join(together[pivot:]))
            la = textwrap.wrap(a, width=width, break_long_words=False)
            lb = textwrap.wrap(b, width=width, break_long_words=False)
            if len(la) <= 2 and len(lb) <= 2:
                choices.append((abs(len(a) - len(b)), "\n".join(la), "\n".join(lb)))
        if choices:
            _, chunks[-2], chunks[-1] = min(choices)
    return chunks


def timestamp(seconds: float, ass: bool = False) -> str:
    scale = 100 if ass else 1000
    ticks = round(seconds * scale)
    hour, rest = divmod(ticks, 3600 * scale)
    minute, rest = divmod(rest, 60 * scale)
    second, fraction = divmod(rest, scale)
    return (
        f"{hour}:{minute:02}:{second:02}.{fraction:02}"
        if ass
        else f"{hour:02}:{minute:02}:{second:02},{fraction:03}"
    )


def subtitles(settings: Settings, cues: list[dict[str, Any]], target: Path) -> None:
    c, r = settings.data["captions"], settings.data["render"]

    def ass_color(value: str) -> str:
        rgb = value[2:]
        return "&H00" + rgb[4:6] + rgb[2:4] + rgb[0:2]

    foreground = ass_color(r["foreground"])
    background = ass_color(r["background"])
    srt = "\n\n".join(
        f"{i}\n{timestamp(x['start'])} --> {timestamp(x['end'])}\n{x['text']}"
        for i, x in enumerate(cues, 1)
    )
    (target / "Captions.srt").write_text(srt + "\n", encoding="utf-8")
    ass = (
        "[Script Info]\nScriptType: v4.00+\n"
        f"PlayResX: {r['width']}\nPlayResY: {r['height']}\nWrapStyle: 2\n\n"
        "[V4+ Styles]\nFormat: Name, Fontname, Fontsize, PrimaryColour, SecondaryColour, OutlineColour, BackColour, Bold, Italic, Underline, StrikeOut, ScaleX, ScaleY, Spacing, Angle, BorderStyle, Outline, Shadow, Alignment, MarginL, MarginR, MarginV, Encoding\n"
        f"Style: Default,{c['font']},{c['size']},{foreground},{foreground},{background},{background},0,0,0,0,100,100,0,0,1,1,0,2,{c['margin_horizontal']},{c['margin_horizontal']},{c['margin_vertical']},1\n\n"
        "[Events]\nFormat: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text\n"
    )
    for x in cues:
        text = x["text"].replace("\n", "\\N")
        ass += f"Dialogue: 0,{timestamp(x['start'], True)},{timestamp(x['end'], True)},Default,,0,0,0,,{text}\n"
    (target / "Captions.ass").write_text(ass, encoding="utf-8")
