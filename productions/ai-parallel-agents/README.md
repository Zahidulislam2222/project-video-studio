# Parallel AI agents + switch-provider: explainer videos

Two videos built with Remotion (React), real WebGL 3D (three.js via `@remotion/three`), and Kokoro `am_puck` narration:

| Composition | Format | Length | Output |
|---|---|---|---|
| `LongVideo` | 1920×1080 landscape | ~4:44 | `out/long-landscape.mp4` |
| `ShortVideo` | 1080×1920 portrait | ~1:17 | `out/short-portrait.mp4` |

The story: one developer runs four projects at once in four VS Code windows (two Claude Code, two Codex). Six context documents cut guessing. When a usage limit hits, the `switch-provider` skill writes a checkpoint handoff, scans it for secrets, and the launcher offers Subscription or OpenRouter. The closing screen shows the portfolio URL.

## Layout

- `script/long.json`, `script/short.json`: narration, split into scenes. `t` is the caption text; `say` is a pronunciation-friendly version sent to TTS.
- `tools/narrate.py`: Kokoro TTS. Writes `public/audio/<id>-narration.wav` and `src/data/<id>.json` with scene, sentence and estimated word timings. Word times are estimated (accurate to about ±150 ms).
- `tools/sound.py`: mixes the narration with an ambient bed, scene whooshes, UI ticks and an impact on "the wall". There is no music.
- `src/scenes/*`: one component per scene. Animations are keyed to spoken words (`useScene().word("handoff")`), so they stay in sync if the script changes.
- `src/components/*`: background grid, 3D orb, VS Code window mock, captions, chapter bar.

## Rebuild

```bash
npm ci
python3 -m pip install kokoro-onnx soundfile scipy
# models dir must contain kokoro-q8.onnx and voices-puck.npz (see below)
python3 tools/narrate.py script/long.json  <models-dir>
python3 tools/narrate.py script/short.json <models-dir>
python3 tools/sound.py long && python3 tools/sound.py short
for v in long short; do ffmpeg -y -i public/audio/$v-mix.wav -af loudnorm=I=-14:TP=-1.5:LRA=11 -ar 48000 /tmp/$v.wav && mv /tmp/$v.wav public/audio/$v-mix.wav; done
tools/render.sh LongVideo out/long-landscape.mp4
tools/render.sh ShortVideo out/short-portrait.mp4
```

`npm run studio` opens the Remotion editor for live preview.

### Voice model

- `kokoro-q8.onnx` is the Apache-2.0 Kokoro-82M v1.0 q8 ONNX model, joined from the npm package `kokoro-q8-shards@1.0.0`. Its sha256 is `fbae9257e1e05ffc727e951ef9b9c98418e6d79f1c9b6b13bd59f5c9028a1478`.
- `voices-puck.npz` holds a single array `am_puck` with shape (510, 1, 256), made from `voices/am_puck.bin` in `kokoro-local-runtime@0.1.0`.

Model files are not committed.

Rendering uses `--gl=swangle` (CPU WebGL), so a GPU isn't needed. Set `REMOTION_BROWSER` if Chrome Headless Shell lives somewhere else.
