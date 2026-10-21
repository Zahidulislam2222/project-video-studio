"""Bounded argument-only child processes with cancellation and preserved diagnostics."""

import asyncio
import json
import os
import re
from contextlib import contextmanager
from pathlib import Path


@contextmanager
def render_lock(settings):
    import fcntl

    path = settings.contained("render.lock")
    with path.open("a") as file:
        try:
            fcntl.flock(file, fcntl.LOCK_EX | fcntl.LOCK_NB)
        except BlockingIOError as exc:
            raise ValueError(
                "Another video is rendering in this workspace; wait or cancel that job"
            ) from exc
        try:
            yield
        finally:
            fcntl.flock(file, fcntl.LOCK_UN)


def python_environment(settings):
    import sys

    return {
        **os.environ,
        "PYTHONPATH": os.pathsep.join(
            dict.fromkeys([str(settings.root), *[str(Path(p).resolve()) for p in sys.path if p]])
        ),
    }


def native_args(args):
    if not str(args[0]).lower().endswith(".exe"):
        return args
    distro = os.environ.get("WSL_DISTRO_NAME")

    def native(value):
        if not isinstance(value, str) or not value.startswith("/"):
            return value
        if re.match(r"^/mnt/[a-z]/", value):
            return value[5].upper() + ":" + value[6:]
        if not distro:
            raise ValueError("Windows tools need WSL_DISTRO_NAME for Linux paths")
        return "\\\\wsl.localhost\\" + distro + value.replace("/", "\\")

    return [args[0], *[native(arg) for arg in args[1:]]]


async def run(
    args: list[str], folder: Path, timeout: float, input_bytes: bytes | None = None, env=None
):
    folder.mkdir(parents=True, exist_ok=True)
    with (folder / "process.log").open("ab") as log:
        process = await asyncio.create_subprocess_exec(
            *native_args(args),
            cwd=folder,
            stdout=asyncio.subprocess.PIPE,
            stderr=log,
            stdin=asyncio.subprocess.PIPE if input_bytes else asyncio.subprocess.DEVNULL,
            env=env,
        )
        try:
            stdout, _ = await asyncio.wait_for(process.communicate(input_bytes), timeout=timeout)
        except (TimeoutError, asyncio.CancelledError):
            if process.returncode is not None:
                raise
            try:
                process.terminate()
            except ProcessLookupError:
                await process.wait()
                raise
            try:
                await asyncio.wait_for(process.wait(), timeout=5)
            except TimeoutError:
                process.kill()
                await process.wait()
            raise
        if process.returncode:
            raise RuntimeError("Media process failed; inspect the private process.log")
        return stdout


async def probe(settings, source: Path, folder: Path):
    if settings.ffprobe:
        result = await run(
            [
                settings.ffprobe,
                "-v",
                "error",
                "-protocol_whitelist",
                "file,pipe",
                "-show_streams",
                "-show_format",
                "-of",
                "json",
                str(source),
            ],
            folder,
            settings.config["render"]["timeout_seconds"],
        )
        return json.loads(result)
    raise ValueError("Configure ffprobe for source inspection and export verification")


def timestamp(seconds: float):
    ticks = round(seconds * 1000)
    h, ticks = divmod(ticks, 3600000)
    m, ticks = divmod(ticks, 60000)
    s, ms = divmod(ticks, 1000)
    return f"{h:02}:{m:02}:{s:02},{ms:03}"


def stream_duration(info, kind):
    stream = next((s for s in info["streams"] if s["codec_type"] == kind), None)
    if not stream:
        raise ValueError("Media has no requested stream")
    if stream.get("duration") is not None:
        return float(stream["duration"])
    tag = stream.get("tags", {}).get("DURATION")
    if tag:
        hours, minutes, seconds = tag.split(":")
        return int(hours) * 3600 + int(minutes) * 60 + float(seconds)
    raise ValueError("Stream duration is unavailable; normalize this recording first")


def srt(cues):
    return (
        "\n\n".join(
            f"{i + 1}\n{timestamp(c['start'])} --> {timestamp(c['end'])}\n{c['text']}"
            for i, c in enumerate(cues)
        )
        + "\n"
    )


def phrases(text: str, width: int):
    result = []
    for sentence in re.split(r"(?<=[.!?])\s+", text.strip()):
        current: list[str] = []
        for word in sentence.split():
            if current and len(" ".join([*current, word])) > width:
                result.append(" ".join(current))
                current = []
            current.append(word)
        if current:
            result.append(" ".join(current))
    return result
