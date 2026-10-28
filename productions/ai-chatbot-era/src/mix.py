"""Original synthesized sound design + final mix and mux.

Usage: python3 src/mix.py out/long
Reads voice.wav, sfx.json, timing.json and picture.mp4; writes mix.wav and final.mp4.
All sounds are generated here (no samples, no licensed music).
"""

import json
import subprocess
import sys
import wave
from pathlib import Path

import numpy as np

SR = 48000
rng = np.random.default_rng(1701)


def read_voice(path):
    with wave.open(str(path)) as f:
        rate, data = f.getframerate(), f.readframes(f.getnframes())
    x = np.frombuffer(data, dtype="<i2").astype(np.float32) / 32768
    t_new = np.arange(int(len(x) * SR / rate)) / SR
    return np.interp(t_new, np.arange(len(x)) / rate, x).astype(np.float32)


def lowpass(x, cutoff):
    a = np.exp(-2 * np.pi * cutoff / SR)
    y = np.empty_like(x)
    acc = 0.0
    for i, v in enumerate(x):
        acc = (1 - a) * v + a * acc
        y[i] = acc
    return y


def whoosh(d=0.7):
    n = int(d * SR)
    t = np.linspace(0, 1, n)
    noise = rng.standard_normal(n).astype(np.float32)
    # Sweep: blend a dark and bright filtered copy across the duration.
    dark, bright = lowpass(noise, 400), noise - lowpass(noise, 2500)
    sweep = dark * (1 - t) + bright * t * 0.6
    env = np.sin(np.pi * t) ** 2
    return sweep * env * 0.9


def hit(d=1.6):
    n = int(d * SR)
    t = np.arange(n) / SR
    boom = np.sin(2 * np.pi * (55 * t + 40 * (1 - np.exp(-t * 18)) / 18)) * np.exp(-t * 3.2)
    shimmer = sum(np.sin(2 * np.pi * f * t) for f in (880, 1320, 1760)) * np.exp(-t * 2.5) * 0.05
    return (boom * 0.8 + shimmer).astype(np.float32)


def pad(seconds):
    """Quiet evolving ambient bed (A minor-ish drone) with slow movement."""
    n = int(seconds * SR)
    t = np.arange(n) / SR
    out = np.zeros(n, dtype=np.float32)
    for f, g in [(110, 0.5), (164.81, 0.35), (220, 0.3), (261.63, 0.18), (329.63, 0.12)]:
        lfo = 0.6 + 0.4 * np.sin(2 * np.pi * (0.03 + f / 20000) * t + f)
        out += (np.sin(2 * np.pi * f * t) + 0.3 * np.sin(2 * np.pi * f * 1.003 * t)) * g * lfo
    pulse = 0.5 + 0.5 * np.sin(2 * np.pi * t * (100 / 60) / 2) ** 8  # gentle ~100bpm swell
    out *= 0.85 + 0.15 * pulse
    fade = np.minimum(1, np.minimum(t / 3, (seconds - t) / 3))
    return out * fade / 2.5


def place(track, clip, at, gain):
    i = int(max(0, at) * SR)
    j = min(len(track), i + len(clip))
    track[i:j] += clip[: j - i] * gain


def main(folder):
    folder = Path(folder)
    timing = json.loads((folder / "timing.json").read_text())
    voice = read_voice(folder / "voice.wav")
    n = int(timing["duration"] * SR) + SR
    voice = np.pad(voice, (0, max(0, n - len(voice))))[:n]
    fx = np.zeros(n, dtype=np.float32)
    w, h = whoosh(), hit()
    for ev in json.loads((folder / "sfx.json").read_text()):
        place(fx, w if ev["k"] == "whoosh" else h, ev["t"] - (0.35 if ev["k"] == "whoosh" else 0), 0.22 if ev["k"] == "whoosh" else 0.28)
    place(fx, h, 0.05, 0.3)
    bed = pad(n / SR)[:n]
    bed = np.pad(bed, (0, n - len(bed)))
    # Duck the bed under speech.
    env = np.convolve(np.abs(voice), np.ones(4800) / 4800, mode="same")
    duck = 1 - 0.55 * np.clip(env / 0.05, 0, 1)
    mix = voice * 1.0 + fx + bed * 0.12 * duck
    mix /= max(1.0, np.abs(mix).max() / 0.95)
    with wave.open(str(folder / "mix.wav"), "wb") as f:
        f.setparams((2, 2, SR, 0, "NONE", "not compressed"))
        st = np.repeat((mix * 32767).astype("<i2")[:, None], 2, axis=1)
        f.writeframes(st.tobytes())
    out = folder / "final.mp4"
    subprocess.run([
        "ffmpeg", "-y", "-loglevel", "error", "-i", str(folder / "picture.mp4"), "-i", str(folder / "mix.wav"),
        "-af", "loudnorm=I=-14:TP=-1.5:LRA=9", "-ar", "48000",
        "-c:v", "copy", "-c:a", "aac", "-b:a", "192k", "-shortest", "-movflags", "+faststart", str(out),
    ], check=True)
    print(out)


if __name__ == "__main__":
    main(sys.argv[1])
