"""Non-musical accents, separate stems and measured final loudness."""

import json
import math
import wave

from .process import run


async def soundtrack(settings, project, root, story):
    if not project.effects:
        return "Voiceover.wav"
    import numpy as np

    cfg, render = settings.config["sound"], settings.config["render"]
    rate = render["audio_rate"]
    samples = round(sum(s["frames"] for s in story) / render["fps"] * rate)
    rng = np.random.default_rng(cfg["seed"])
    events = []
    for i, shot in enumerate(story):
        length = round(rate * (cfg["whoosh_seconds"] if i == 0 else cfg["click_seconds"]))
        noise = rng.uniform(-1, 1, length)
        noise = np.convolve(
            noise, np.ones(cfg["noise_smoothing"]) / cfg["noise_smoothing"], mode="same"
        )
        pulse = noise * np.sin(np.linspace(0, math.pi, length)) ** (2 if i == 0 else 8)
        peak = max(float(np.max(np.abs(pulse))), 1e-9)
        pulse *= 10 ** (cfg["gain_db"] / 20) / peak
        events.append((round(shot["start"] * rate), pulse))
    with wave.open(str(root / "Effects.wav"), "wb") as file:
        file.setparams((2, 2, rate, 0, "NONE", "not compressed"))
        for start in range(0, samples, rate):
            block = np.zeros(min(rate, samples - start))
            for position, pulse in events:
                lo, hi = max(start, position), min(start + len(block), position + len(pulse))
                if hi > lo:
                    block[lo - start : hi - start] += pulse[lo - position : hi - position]
            pcm = (np.clip(block, -1, 1) * 32767).astype("<i2")
            file.writeframes(np.repeat(pcm[:, None], 2, axis=1).tobytes())
    await run(
        [
            settings.ffmpeg,
            "-hide_banner",
            "-n",
            "-i",
            "Voiceover.wav",
            "-i",
            "Effects.wav",
            "-filter_complex",
            f"[0:a][1:a]amix=inputs=2:normalize=0:duration=first,loudnorm=I={render['loudness']}:TP={render['true_peak']}:LRA={render['loudness_range']}",
            "-ar",
            str(rate),
            "-ac",
            "2",
            "Soundtrack.wav",
        ],
        root,
        render["timeout_seconds"],
    )
    return "Soundtrack.wav"


async def scan(settings, source, root):
    cfg = settings.config["render"]
    log = root / "process.log"
    offset = log.stat().st_size if log.exists() else 0
    await run(
        [
            settings.ffmpeg,
            "-hide_banner",
            "-i",
            str(source),
            "-vn",
            "-af",
            f"loudnorm=I={cfg['loudness']}:TP={cfg['true_peak']}:LRA={cfg['loudness_range']}:print_format=json",
            "-f",
            "null",
            "-",
        ],
        root,
        cfg["timeout_seconds"],
    )
    with log.open("rb") as file:
        file.seek(offset)
        text = file.read().decode(errors="replace")
    start, end = text.rfind("{"), text.rfind("}")
    result = json.loads(text[start : end + 1])
    return result


async def normalize(settings, source, root):
    cfg = settings.config["render"]
    measured = await scan(settings, source, root)
    if not math.isfinite(float(measured["input_i"])):
        return source
    filtergraph = f"loudnorm=I={cfg['loudness']}:TP={cfg['true_peak']}:LRA={cfg['loudness_range']}:measured_I={measured['input_i']}:measured_TP={measured['input_tp']}:measured_LRA={measured['input_lra']}:measured_thresh={measured['input_thresh']}:offset={measured['target_offset']}:linear=true"
    await run(
        [
            settings.ffmpeg,
            "-hide_banner",
            "-n",
            "-i",
            str(source),
            "-af",
            filtergraph,
            "-ar",
            str(cfg["audio_rate"]),
            "-ac",
            "2",
            "MasterAudio.wav",
        ],
        root,
        cfg["timeout_seconds"],
    )
    (root / "AudioNormalization.json").write_text(json.dumps(measured, indent=2))
    return root / "MasterAudio.wav"


async def measure(settings, source, root):
    cfg = settings.config["render"]
    result = await scan(settings, source, root)
    loudness, peak = float(result["input_i"]), float(result["input_tp"])
    silent = not math.isfinite(loudness)
    valid = silent or not (
        abs(loudness - cfg["loudness"]) > cfg["loudness_tolerance"]
        or peak > cfg["true_peak"] + cfg["peak_tolerance"]
    )
    report = {
        "integrated_lufs": None if silent else loudness,
        "true_peak_dbtp": peak if math.isfinite(peak) else None,
        "silent": silent,
        "within_limits": valid,
    }
    (root / "AudioVerification.json").write_text(json.dumps(report, indent=2))
    if not valid:
        raise ValueError(
            "Measured audio exceeds configured loudness/peak limits; inspect AudioVerification.json"
        )
    return report
