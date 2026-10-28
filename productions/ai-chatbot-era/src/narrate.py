"""Synthesize narration per sentence with Kokoro and write a timing map for the renderer.

Usage: python3 src/narrate.py scripts/long.json out/long
Writes voice.wav (24 kHz mono) and timing.json (scene, beat and word times in seconds).
"""

import hashlib
import json
import re
import sys
import wave
from pathlib import Path

import numpy as np
import onnxruntime
from kokoro_onnx import Kokoro

ROOT = Path(__file__).resolve().parents[3]
MODEL = ROOT / ".runtime/models/kokoro-v1.0.int8.onnx"
VOICES = ROOT / ".runtime/models/voices-v1.0.bin"

LEAD_IN = 0.6  # silence before the first scene
BEAT_GAP = 0.32  # between beats inside a scene
SENTENCE_GAP = 0.18  # between sentences inside a beat
SCENE_GAP = 0.85  # extra breathing room at scene changes

# Spoken form -> on-screen caption form.
DISPLAY = [
    ("zahidul islam dot com", "zahidul-islam.com"),
    ("twenty-four seven", "24/7"),
    ("twenty-nine dollars", "$29"),
    ("twenty twenty-nine", "2029"),
    ("two point three million", "2.3 million"),
    ("seven hundred", "700"),
    ("eleven minutes", "11 minutes"),
    ("fourteen percent", "14%"),
    ("thirty-four percent", "34%"),
    ("eighty percent", "80%"),
    ("five thousand", "5,000"),
    ("twenty hoodies", "20 hoodies"),
    ("two in the morning", "2 AM"),
    ("two seconds", "2 seconds"),
    ("two thirds", "two-thirds"),
    ("M.I.T.", "MIT"),
    ("C.E.O.", "CEO"),
]


def display(text):
    for spoken, shown in DISPLAY:
        text = text.replace(spoken, shown)
    return text


def check_assets():
    cfg = json.loads((ROOT / "settings.json").read_text())
    for key, path in [("model", MODEL), ("voices", VOICES)]:
        if hashlib.sha256(path.read_bytes()).hexdigest() != cfg[key + "_sha256"]:
            raise SystemExit(f"{path.name} failed the settings.json integrity check")


def sentences(beat):
    parts = re.split(r"(?<=[.?!])\s+(?=[A-Z0-9])", beat.strip())
    return [p for p in parts if p]


def trim(audio, rate, threshold=0.012):
    loud = np.flatnonzero(np.abs(audio) > threshold)
    if not len(loud):
        return audio
    pad = int(0.03 * rate)
    return audio[max(0, loud[0] - pad) : loud[-1] + pad]


def internal_gaps(audio, rate, minimum=0.09):
    """Return midpoints (seconds) of silent stretches inside the clip."""
    hop = int(0.01 * rate)
    frames = len(audio) // hop
    energy = np.sqrt((audio[: frames * hop].reshape(frames, hop) ** 2).mean(axis=1))
    quiet = energy < 0.01
    gaps, start = [], None
    for i, q in enumerate(quiet):
        if q and start is None:
            start = i
        elif not q and start is not None:
            if (i - start) * 0.01 >= minimum and start > 5:
                gaps.append(((start + i) / 2 * 0.01, (i - start) * 0.01))
            start = None
    return gaps


def word_times(text, audio, rate, offset):
    """Distribute words across a sentence, snapping comma clauses to detected pauses."""
    clauses = [c.strip() for c in re.split(r"(?<=[,;:])\s+", text) if c.strip()]
    duration = len(audio) / rate
    bounds = [0.0]
    gaps = internal_gaps(audio, rate)
    if len(clauses) > 1 and len(gaps) >= len(clauses) - 1:
        chosen = sorted(sorted(gaps, key=lambda g: -g[1])[: len(clauses) - 1])
        bounds += [g[0] for g in chosen]
    else:
        weights = [len(c) for c in clauses]
        acc = 0
        for w in weights[:-1]:
            acc += w
            bounds.append(duration * acc / sum(weights))
    bounds.append(duration)
    words = []
    for clause, a, b in zip(clauses, bounds, bounds[1:]):
        tokens = clause.split()
        weights = [len(t) + 2 for t in tokens]
        total, acc = sum(weights), 0
        for tok, w in zip(tokens, weights):
            s = a + (b - a) * acc / total
            acc += w
            e = a + (b - a) * acc / total
            words.append({"w": tok, "s": round(offset + s, 3), "e": round(offset + e, 3)})
    return words


def main(script_path, out_dir):
    check_assets()
    script = json.loads(Path(script_path).read_text())
    out = Path(out_dir)
    out.mkdir(parents=True, exist_ok=True)
    options = onnxruntime.SessionOptions()
    options.intra_op_num_threads = 4
    engine = Kokoro.from_session(
        onnxruntime.InferenceSession(str(MODEL), sess_options=options, providers=["CPUExecutionProvider"]),
        str(VOICES),
    )
    rate = 24000
    chunks = [np.zeros(int(LEAD_IN * rate), dtype=np.float32)]
    cursor = LEAD_IN
    timing = {"id": script["id"], "title": script["title"], "ratio": script["ratio"], "scenes": []}
    for si, scene in enumerate(script["scenes"]):
        entry = {"id": scene["id"], "chapter": scene.get("chapter", ""), "start": round(cursor, 3), "beats": []}
        for bi, beat in enumerate(scene["beats"]):
            b = {"text": display(beat), "start": round(cursor, 3), "words": []}
            for k, sentence in enumerate(sentences(beat)):
                audio, sr = engine.create(sentence, voice=script["voice"], speed=script["speed"], lang="en-us")
                assert sr == rate
                audio = trim(np.asarray(audio, dtype=np.float32), rate)
                b["words"] += word_times(display(sentence), audio, rate, cursor)
                chunks.append(audio)
                cursor += len(audio) / rate
                if k < len(sentences(beat)) - 1:
                    chunks.append(np.zeros(int(SENTENCE_GAP * rate), dtype=np.float32))
                    cursor += SENTENCE_GAP
            b["end"] = round(cursor, 3)
            entry["beats"].append(b)
            gap = BEAT_GAP if bi < len(scene["beats"]) - 1 else SCENE_GAP
            chunks.append(np.zeros(int(gap * rate), dtype=np.float32))
            cursor += gap
            print(f"  {scene['id']}[{bi}] {b['end'] - b['start']:.2f}s", flush=True)
        entry["end"] = round(cursor, 3)
        timing["scenes"].append(entry)
    tail = 2.5 if script["id"] == "long" else 2.0
    chunks.append(np.zeros(int(tail * rate), dtype=np.float32))
    cursor += tail
    timing["duration"] = round(cursor, 3)
    timing["scenes"][-1]["end"] = timing["duration"]
    pcm = (np.clip(np.concatenate(chunks), -1, 1) * 32767).astype("<i2")
    with wave.open(str(out / "voice.wav"), "wb") as f:
        f.setparams((1, 2, rate, 0, "NONE", "not compressed"))
        f.writeframes(pcm.tobytes())
    (out / "timing.json").write_text(json.dumps(timing, indent=1))
    print(f"{script['id']}: {timing['duration']:.1f}s")


if __name__ == "__main__":
    main(*sys.argv[1:3])
