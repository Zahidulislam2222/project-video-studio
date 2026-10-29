"""Build the final audio: narration + ambient bed + transition whooshes + UI ticks (no music).

Usage: python3 tools/sound.py <id>   (reads src/data/<id>.json and public/audio/<id>-narration.wav)
Writes public/audio/<id>-mix.wav (loudness normalised later by ffmpeg in tools/render.sh).
"""
import json
import sys
from pathlib import Path

import numpy as np
import soundfile as sf

ROOT = Path(__file__).resolve().parent.parent
SR = 48000
HOLD = 3.0  # outro hold seconds (matches OUTRO_HOLD frames / 30)
rng = np.random.default_rng(7)


def onepole(x, cutoff):
    a = 1 - np.exp(-2 * np.pi * cutoff / SR)
    from scipy.signal import lfilter
    return lfilter([a], [1, -(1 - a)], x)


def whoosh(dur=0.9, up=True):
    n = int(dur * SR)
    t = np.linspace(0, 1, n)
    noise = rng.standard_normal(n)
    # sweep a resonant band through the noise
    from scipy.signal import butter, sosfilt
    out = np.zeros(n)
    seg = 256
    f0, f1 = (300, 4500) if up else (4500, 300)
    zi = None
    for s in range(0, n, seg):
        f = f0 * (f1 / f0) ** (s / n)
        sos = butter(2, [max(40, f * 0.6), min(SR / 2 - 100, f * 1.5)], btype="band", fs=SR, output="sos")
        chunk, zi = sosfilt(sos, noise[s:s + seg], zi=zi if zi is not None else np.zeros((sos.shape[0], 2)))
        out[s:s + seg] = chunk
    env = np.sin(np.pi * t) ** 2 * (t ** 0.3)
    return out * env / (np.max(np.abs(out * env)) + 1e-9)


def tick(freq=1500, dur=0.07):
    n = int(dur * SR)
    t = np.arange(n) / SR
    return np.sin(2 * np.pi * freq * t) * np.exp(-t * 60) + 0.4 * np.sin(2 * np.pi * freq * 2 * t) * np.exp(-t * 90)


def thud(dur=0.6):
    n = int(dur * SR)
    t = np.arange(n) / SR
    f = 90 * np.exp(-t * 4) + 40
    ph = 2 * np.pi * np.cumsum(f) / SR
    return np.sin(ph) * np.exp(-t * 6) + 0.25 * rng.standard_normal(n) * np.exp(-t * 30)


def riser(dur=2.0):
    w = whoosh(dur, up=True)
    n = len(w)
    t = np.linspace(0, 1, n)
    return w * t


def main():
    vid = sys.argv[1]
    data = json.loads((ROOT / "src" / "data" / f"{vid}.json").read_text())
    nar, sr = sf.read(ROOT / "public" / "audio" / f"{vid}-narration.wav")
    from scipy.signal import resample_poly
    nar = resample_poly(nar, SR, sr)
    total = int((data["duration"] + HOLD) * SR) + SR
    mix_n = np.zeros(total)
    mix_n[: len(nar)] += nar
    fx = np.zeros(total)

    def place(sig, at, gain):
        i = int(max(0, at) * SR)
        j = min(total, i + len(sig))
        fx[i:j] += sig[: j - i] * gain

    for k, sc in enumerate(data["scenes"]):
        if k > 0:
            place(whoosh(0.9, up=k % 2 == 0), sc["start"] - 0.45, 0.22)
        for i, se in enumerate(sc["sentences"]):
            if i > 0:
                place(tick(1400 + 200 * (i % 3)), se["start"] - 0.05, 0.07)
        for se in sc["sentences"]:
            for w in se["words"]:
                if sc["id"] == "limit" and data["id"] == "short" and w["w"].lower().startswith("limit,"):
                    place(thud(), w["s"], 0.5)
                lw = w["w"].lower().strip(".,")
                if sc["id"] == "limit" and lw == "wall":
                    place(thud(), w["s"], 0.5)
        if sc["id"] == "outro":
            place(riser(1.6), sc["start"] + 0.1, 0.12)
    # ambient bed: filtered brown-ish noise + soft low drone, slow swell
    t = np.arange(total) / SR
    bed = onepole(rng.standard_normal(total), 220)
    bed = bed / (np.max(np.abs(bed)) + 1e-9)
    drone = 0.5 * np.sin(2 * np.pi * 55 * t) + 0.3 * np.sin(2 * np.pi * 82.5 * t + 1) + 0.15 * np.sin(2 * np.pi * 110.3 * t)
    lfo = 0.75 + 0.25 * np.sin(2 * np.pi * t / 17)
    amb = (0.6 * bed + 0.4 * drone) * lfo
    fade = np.minimum(1, t / 2.5) * np.minimum(1, (total / SR - t) / 2.5)
    amb *= fade * 0.06
    out = mix_n * 1.0 + fx + amb
    out = out / (np.max(np.abs(out)) + 1e-9) * 0.95
    sf.write(ROOT / "public" / "audio" / f"{vid}-mix.wav", out.astype(np.float32), SR, subtype="PCM_24")
    print(vid, "mix", round(total / SR, 2), "s")


if __name__ == "__main__":
    main()
