"""Bounded offline speech recognition; downloaded models are explicitly configured."""

import json
import os
import sys
from pathlib import Path

from .process import python_environment, run


async def transcribe(settings, source, output, language=None):
    model = os.environ.get("STUDIO_TRANSCRIPTION_MODEL")
    if not model or not Path(model).is_dir():
        raise ValueError(
            "Configure an installed offline transcription model, or supply timed SRT captions"
        )
    output.mkdir(parents=True, exist_ok=False)
    await run(
        [
            settings.ffmpeg,
            "-hide_banner",
            "-n",
            "-protocol_whitelist",
            "file,pipe",
            "-i",
            str(source),
            "-map",
            "0:a:0",
            "-vn",
            "-ac",
            "1",
            "-ar",
            str(settings.config["transcription"]["audio_rate"]),
            "-c:a",
            "pcm_s16le",
            str(output / "Input.wav"),
        ],
        output,
        settings.config["transcription"]["timeout_seconds"],
    )
    (output / "Request.json").write_text(
        json.dumps({"source": str(output / "Input.wav"), "model": model, "language": language})
    )
    await run(
        [sys.executable, "-m", "studio_v2.transcription", str(output)],
        output,
        settings.config["transcription"]["timeout_seconds"],
        env=python_environment(settings),
    )
    return json.loads((output / "Transcript.json").read_text())


def recognize(folder):
    import hashlib
    import wave

    import numpy as np
    import onnxruntime

    onnxruntime.disable_telemetry_events()
    from faster_whisper import WhisperModel

    from .settings import Settings

    settings = Settings.load()
    request = json.loads((folder / "Request.json").read_text())
    cfg = settings.config["transcription"]
    model_path = Path(request["model"])
    manifest = json.loads((model_path / "ModelIntegrity.json").read_text())
    for name, expected in manifest["files"].items():
        path = (model_path / name).resolve()
        if (
            not path.is_relative_to(model_path.resolve())
            or hashlib.sha256(path.read_bytes()).hexdigest() != expected
        ):
            raise ValueError("Transcription model integrity check failed")
    model = WhisperModel(
        request["model"],
        device="cpu",
        compute_type="int8",
        cpu_threads=settings.config["render"]["threads"],
        num_workers=1,
        local_files_only=True,
    )
    with wave.open(request["source"], "rb") as source:
        if (
            source.getnchannels() != 1
            or source.getsampwidth() != 2
            or source.getframerate() != cfg["audio_rate"]
        ):
            raise ValueError("Transcription requires normalized mono PCM")
        audio = (
            np.frombuffer(source.readframes(source.getnframes()), dtype="<i2").astype(np.float32)
            / 32768
        )
    segments, info = model.transcribe(
        audio,
        beam_size=cfg["beam_size"],
        language=request["language"],
        word_timestamps=True,
        vad_filter=True,
        condition_on_previous_text=False,
    )
    cues = []
    current = None
    for segment in segments:
        for word in segment.words or []:
            text = word.word.strip()
            if not text or word.end <= word.start:
                continue
            if current and (
                len(current["text"] + " " + text) > settings.config["render"]["caption_characters"]
                or word.end - current["start"] > cfg["caption_seconds"]
            ):
                cues.append(current)
                current = None
            if current:
                current["text"] += " " + text
                current["end"] = word.end
            else:
                current = {"start": word.start, "end": word.end, "text": text}
    if current:
        cues.append(current)
    if not cues:
        raise ValueError(
            "No speech was detected; supply a corrected transcript or another recording"
        )
    (folder / "Transcript.json").write_text(
        json.dumps(
            {
                "language": info.language,
                "cues": cues,
                "method": "Local Whisper speech recognition; transcript and timing require review",
            },
            indent=2,
        )
    )


if __name__ == "__main__":
    recognize(Path(sys.argv[1]).resolve())
