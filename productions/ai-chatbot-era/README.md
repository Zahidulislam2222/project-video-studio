# AI Chatbot Era — explainer production

Two edits from one engine:

| Edit | Ratio | Length | Script |
|------|-------|--------|--------|
| Long | 1920×1080 landscape | ~5:00 | `scripts/long.json` |
| Short | 1080×1920 portrait | ~1:21 | `scripts/short.json` |

Voice: Kokoro `am_puck` (offline, assets verified against `settings.json` hashes).

## Pipeline

```bash
python3 src/narrate.py scripts/long.json out/long     # voice.wav + timing.json (word-level cues)
node src/render.js long stills 12 40 95               # review frames -> out/long/stills
node src/render.js long events                        # transition SFX cue list
node src/render.js long video 4                       # picture.mp4 (4 parallel Chromium workers)
python3 src/mix.py out/long                           # synthesized SFX + ambient bed, -14 LUFS, final.mp4
```

Replace `long` with `short` for the portrait edit.

## How it works

- `src/narrate.py` synthesizes each sentence, measures pauses, and writes scene/beat/word times.
- `src/scenes.js` draws every scene as a pure function of time. Visuals are bound to named cues
  (`'b2:inventory'` = the moment the word "inventory" is spoken in beat 2), so editing the script and
  re-running narration keeps graphics in sync.
- `src/bg3d.js` is the persistent three.js world (neural core, grid floor, star tunnel, glass solids);
  the camera keeps flying forward and each scene sets a preset.
- `src/main.js` composites the 3D layer, scene graphics, chapter "level" cards, progress bar, word-highlighted
  captions and light-sweep transitions.
- `src/mix.py` generates all sound (whooshes, hits, ambient pad) procedurally — no samples or licensed music.

## Sources shown on screen

- Klarna press release, 27 Feb 2024 — 2.3M conversations, two-thirds of chats, ≈700 FTE, 11 → <2 min (company-reported).
- Brynjolfsson, Li & Raymond, "Generative AI at Work", *Quarterly Journal of Economics* 140(2), 2025 — +14% issues/hour, +34% for novice agents (5,179 agents).
- Gartner press release, 5 Mar 2025 — agentic AI to resolve 80% of common customer service issues by 2029 (prediction).
- Moffatt v. Air Canada, 2024 BCCRT 149 (14 Feb 2024) — airline liable for its chatbot's wrong refund information.
- Klarna CEO to Bloomberg, May 2025 — hiring human agents again after quality concerns.

The cost chart, "who handles what" split, compounding-advantage chart and the admin/invoice UIs are labelled
illustrative/demo data on screen; they are not measurements.

The CTA uses screenshots of a local production build of the My-Portfolio repo (`assets/`).

## Third-party assets

- Inter, Space Grotesk, JetBrains Mono (`fonts/`) — SIL Open Font License 1.1.
- three.js r160 (`vendor/`) — MIT License.
