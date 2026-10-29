"""Generate am_puck narration plus scene/sentence/word timings for the Remotion compositions.

Usage: python3 tools/narrate.py <script.json> <models_dir>
Writes public/audio/<id>-narration.wav and src/data/<id>.json.
Word times are estimated: speech regions are found by energy, and words inside a
region are spread by phoneme count. Expect roughly +/-150 ms accuracy.
"""
import json
import re
import sys
from pathlib import Path

import numpy as np
import soundfile as sf
from kokoro_onnx import Kokoro

ROOT = Path(__file__).resolve().parent.parent
VOICE = "am_puck"
SPEED = 1.04
SR = 24000
SENTENCE_GAP = 0.32
SCENE_LEAD = 0.45
SCENE_TAIL = 0.75
FPS = 30


def speech_regions(audio, min_gap=0.09, thresh_db=-38):
    hop = int(0.01 * SR)
    frames = len(audio) // hop
    rms = np.array([np.sqrt(np.mean(audio[i * hop:(i + 1) * hop] ** 2) + 1e-12) for i in range(frames)])
    db = 20 * np.log10(rms + 1e-9)
    voiced = db > thresh_db
    regions, start, silent = [], None, 0
    for i, v in enumerate(voiced):
        if v:
            if start is None:
                start = i
            silent = 0
        elif start is not None:
            silent += 1
            if silent * 0.01 >= min_gap:
                regions.append([start * 0.01, (i - silent + 1) * 0.01])
                start, silent = None, 0
    if start is not None:
        regions.append([start * 0.01, (frames - silent) * 0.01])
    return regions


def word_weights(kokoro, words):
    out = []
    for w in words:
        clean = re.sub(r"[^A-Za-z0-9'$/-]", "", w) or w
        try:
            ph = kokoro.tokenizer.phonemize(clean.replace("/", "slash ").replace("$", "dollar ").replace("-", " "), "en-us")
            n = len(ph.replace(" ", ""))
        except Exception:
            n = len(clean)
        out.append(max(2, n))
    return out


def clause_groups(words):
    """Split caption words into clauses at punctuation so they can map to speech regions."""
    groups, cur = [], []
    for i, w in enumerate(words):
        cur.append(i)
        if re.search(r"[,.;:?!]$", w):
            groups.append(cur)
            cur = []
    if cur:
        groups.append(cur)
    return groups


def time_words(kokoro, text, audio):
    words = text.split()
    weights = word_weights(kokoro, words)
    regions = speech_regions(audio)
    if not regions:
        regions = [[0.0, len(audio) / SR]]
    groups = clause_groups(words)
    # Merge regions down to clause count when they line up; otherwise one span.
    spans = []
    if len(regions) == len(groups):
        spans = list(zip(groups, regions))
    elif len(regions) > len(groups) and len(groups) > 1:
        # Keep the largest gaps as clause boundaries.
        gaps = sorted(range(len(regions) - 1), key=lambda i: regions[i + 1][0] - regions[i][1], reverse=True)
        cut = sorted(gaps[: len(groups) - 1])
        merged, s = [], 0
        for c in cut + [len(regions) - 1]:
            merged.append([regions[s][0], regions[c][1]])
            s = c + 1
        spans = list(zip(groups, merged))
    else:
        spans = [(list(range(len(words))), [regions[0][0], regions[-1][1]])]
    timed = [None] * len(words)
    for idxs, (a, b) in spans:
        total = sum(weights[i] for i in idxs)
        t = a
        for i in idxs:
            d = (b - a) * weights[i] / total
            timed[i] = {"w": words[i], "s": round(t, 3), "e": round(t + d, 3)}
            t += d
    return timed


def main():
    script = json.loads(Path(sys.argv[1]).read_text())
    models = Path(sys.argv[2])
    kokoro = Kokoro(str(models / "kokoro-q8.onnx"), str(models / "voices-puck.npz"))
    chunks, scenes, t = [], [], 0.0
    for scene in script["scenes"]:
        s_start = t
        chunks.append(np.zeros(int(SCENE_LEAD * SR), np.float32))
        t += SCENE_LEAD
        sentences = []
        for k, line in enumerate(scene["lines"]):
            text = line if isinstance(line, str) else line["t"]
            say = line if isinstance(line, str) else line["say"]
            audio, sr = kokoro.create(say, voice=VOICE, speed=SPEED, lang="en-us")
            assert sr == SR
            audio = audio.astype(np.float32)
            words = time_words(kokoro, text, audio)
            for w in words:
                w["s"] = round(w["s"] + t, 3)
                w["e"] = round(w["e"] + t, 3)
            dur = len(audio) / SR
            sentences.append({"text": text, "start": round(t, 3), "end": round(t + dur, 3), "words": words})
            chunks.append(audio)
            t += dur
            if k < len(scene["lines"]) - 1:
                chunks.append(np.zeros(int(SENTENCE_GAP * SR), np.float32))
                t += SENTENCE_GAP
        chunks.append(np.zeros(int(SCENE_TAIL * SR), np.float32))
        t += SCENE_TAIL
        scenes.append({"id": scene["id"], "chapter": scene["chapter"], "start": round(s_start, 3), "end": round(t, 3), "sentences": sentences})
        print(f"{scene['id']:8s} {s_start:7.2f} -> {t:7.2f}")
    full = np.concatenate(chunks)
    peak = np.max(np.abs(full))
    full = full / peak * 0.89
    out_audio = ROOT / "public" / "audio" / f"{script['id']}-narration.wav"
    out_audio.parent.mkdir(parents=True, exist_ok=True)
    sf.write(out_audio, full, SR, subtype="PCM_16")
    data = {"id": script["id"], "fps": FPS, "duration": round(t, 3), "durationInFrames": int(np.ceil(t * FPS)), "scenes": scenes}
    out = ROOT / "src" / "data" / f"{script['id']}.json"
    out.write_text(json.dumps(data, indent=1))
    print("total", round(t, 2), "s")


if __name__ == "__main__":
    main()
