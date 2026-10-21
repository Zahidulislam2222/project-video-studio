"""Male stock narration with captions bound to actual synthesized phrase samples."""

import hashlib
import json
import sys
import wave

from .process import phrases


def synthesize(settings, project, shot, folder):
    if not settings.model or not settings.voices:
        raise ValueError("Configure the offline model and voice pack, or supply recorded audio")
    legacy = __import__("json").loads((settings.root / "settings.json").read_text())
    for key, path in [("model", settings.model), ("voices", settings.voices)]:
        if hashlib.sha256(path.read_bytes()).hexdigest() != legacy[key + "_sha256"]:
            raise ValueError("Offline voice asset integrity check failed")
    if settings.runtime and str(settings.runtime) not in sys.path:
        sys.path.append(str(settings.runtime))
    import numpy as np
    import onnxruntime

    onnxruntime.disable_telemetry_events()
    from kokoro_onnx import Kokoro

    options = onnxruntime.SessionOptions()
    options.intra_op_num_threads = settings.config["render"]["threads"]
    options.inter_op_num_threads = 1
    engine = Kokoro.from_session(
        onnxruntime.InferenceSession(
            str(settings.model), sess_options=options, providers=["CPUExecutionProvider"]
        ),
        str(settings.voices),
    )
    voice = project.voice
    if voice not in settings.config["voices"] or voice not in engine.get_voices():
        raise ValueError("Approved male voice is unavailable")
    data = bytearray()
    cues = []
    sr = None
    for phrase in phrases(shot.narration, settings.config["render"]["caption_characters"]):
        audio, rate = engine.create(
            phrase,
            voice=voice,
            speed=settings.config["delivery"][project.delivery],
            lang=settings.config["voices"][voice],
        )
        if sr and sr != rate:
            raise ValueError("Narration sample rate changed")
        sr = rate
        start = len(data) / (2 * sr)
        data.extend((np.clip(audio, -1, 1) * 32767).astype("<i2").tobytes())
        cues.append({"start": start, "end": len(data) / (2 * sr), "text": phrase})
        data.extend(b"\0\0" * round(sr * settings.config["render"]["phrase_pause"]))
    if sr is None:
        raise ValueError("No spoken content")
    path = folder / "voice.wav"
    with wave.open(str(path), "wb") as f:
        f.setparams((1, 2, sr, 0, "NONE", "not compressed"))
        f.writeframes(data)
    return path, len(data) / (2 * sr), cues


if __name__ == "__main__":
    from pathlib import Path

    from .models import Project, Shot
    from .settings import Settings

    folder = Path(sys.argv[1]).resolve()
    request = json.loads((folder / "NarrationRequest.json").read_text())
    path, seconds, cues = synthesize(
        Settings.load(),
        Project.model_validate(request["project"]),
        Shot.model_validate(request["shot"]),
        folder,
    )
    (folder / "Narration.json").write_text(json.dumps({"seconds": seconds, "cues": cues}))
