"""Offline stock male narration; delivery changes pacing, not emotion prompts."""

from __future__ import annotations

import math
import wave
from pathlib import Path
from typing import Any

from config import Film, Settings
from media_tools import caption_chunks


def write_wav(path: Path, data: bytes | bytearray, rate: int) -> None:
    with wave.open(str(path), "wb") as wav:
        wav.setparams((1, 2, rate, 0, "NONE", "not compressed"))
        wav.writeframes(data)


def synthesize(
    settings: Settings, film: Film, output: Path
) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    import numpy as np
    from kokoro_onnx import Kokoro

    engine = Kokoro(
        str(settings.root / settings.data["model"]),
        str(settings.root / settings.data["voices"]),
    )
    if film.voice not in engine.get_voices():
        raise ValueError("Configured male voice missing from installed voice pack")
    render, captions = settings.data["render"], settings.data["captions"]
    timeline, cues = [], []
    cursor, master = 0.0, bytearray()
    rate = None
    for scene in film.scenes:
        preset = settings.delivery[scene.delivery]
        scene_pcm = bytearray()
        for index, sentence in enumerate(scene.sentences):
            spoken = sentence
            for key, value in film.pronunciation.items():
                spoken = spoken.replace(key, value)
            audio, sr = engine.create(
                spoken,
                voice=film.voice,
                speed=preset.speed,
                lang=settings.data["male_voices"][film.voice],
                sentence_pause=preset.sentence_pause,
                clause_pause=preset.clause_pause,
            )
            if rate is not None and rate != sr:
                raise ValueError("Narration engine changed sample rate")
            rate = sr
            if not index:
                scene_pcm.extend(b"\0\0" * round(sr * render["scene_lead"]))
            start = cursor + len(scene_pcm) / (2 * sr)
            pcm = (np.clip(audio, -1, 1) * 32767).astype("<i2").tobytes()
            scene_pcm.extend(pcm)
            end = cursor + len(scene_pcm) / (2 * sr)
            chunks = caption_chunks(sentence, captions["line_characters"])
            weight, at = sum(len(c) for c in chunks), start
            for chunk in chunks:
                stop = at + (end - start) * len(chunk) / weight
                if stop - at < captions["minimum_seconds"]:
                    raise ValueError(
                        "Caption is too brief; revise narration text or delivery speed"
                    )
                cues.append({"start": at, "end": stop, "text": chunk})
                at = stop
            scene_pcm.extend(b"\0\0" * round(sr * preset.gap))
        if rate is None:
            raise ValueError("Narration produced no audio")
        scene_pcm.extend(b"\0\0" * round(rate * render["scene_tail"]))
        frames = math.ceil(len(scene_pcm) / (2 * rate) * render["fps"])
        target = round(frames / render["fps"] * rate)
        scene_pcm.extend(b"\0\0" * (target - len(scene_pcm) // 2))
        write_wav(output / "media" / (scene.ident + ".wav"), scene_pcm, rate)
        timeline.append(
            {
                "id": scene.ident,
                "title": scene.title,
                "subtitle": scene.subtitle,
                "start": cursor,
                "duration": frames / render["fps"],
                "frames": frames,
                "role": scene.role,
                "motion": scene.motion,
            }
        )
        master.extend(scene_pcm)
        cursor += frames / render["fps"]
        print("Narration: " + scene.ident, flush=True)
    if rate is None or cursor > settings.data["limits"]["max_duration_seconds"]:
        raise ValueError("Narration empty or exceeds configured duration limit")
    write_wav(output / "narration-raw.wav", master, rate)
    return timeline, cues
