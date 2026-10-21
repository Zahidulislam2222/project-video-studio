# Project Video Studio

A reusable local workspace for project videos with English male narration, timed captions, genuine footage, clean and captioned 1080p exports, and editable timelines. It uses the existing Windows/WSL workstation and offline Kokoro model. No paid voice API or upload service is needed.

This section documents the retained v1 workflow. For current production, use [the v2 guide](../README-V2.md).

Double-click **Start Studio.cmd** to open the menu. Choose **Male voice previews** to compare the four delivery presets, **New project** to create a project, or **Build project** to export it.

## Create another project

1. Choose a name such as `my-next-project` in the menu, then select `short` or `long`.
2. Edit `projects/my-next-project/film.json`: title, author, narration, pronunciation, scene titles, delivery, motion and sound. The templates contain example narration for replacement, not claims about your project.
3. Put approved screen recordings or images in that project's `assets/` folder. Set each scene's `media` to a relative filename such as `assets/overview.mp4`. A `null` media value produces a title card.
4. Build the project. Each run gets its own folder under `projects/my-next-project/exports/`; earlier exports are preserved.
5. Review the picture and voice before publishing. `Verification.json` records the format, duration, exact frames, full decoding, captions and timeline checks. A failed verification leaves the run intact and does not advance `latest-export.json`.

Short films target **60–120 seconds**, in portrait by default, with an intro up to 6 seconds and an ending up to 7 seconds. Long films target **240–300 seconds**, in widescreen, with an intro up to 8 seconds and an ending up to 10 seconds. Format sizes, time budgets, template paths and default motion belong to `settings.json` → `formats`; additional named formats can be added there. Use `custom` for a different duration and the original global render defaults. Existing films without a format retain their original behavior.

Use `plan` for a rough word-count estimate. Actual narration determines scene length, and a build rejects scripts outside the selected range or with an overlong intro/ending. Shorten or expand the story using verified facts; the engine does not add filler or accelerate speech to force a duration. Record enough footage for each spoken scene. Use OBS or approved browser captures for real flows; this setup does not log into project accounts automatically.

## Motion design and non-musical sound

New shorts use `dynamic` motion and longer films use `calm`. Both provide eased title reveals, staggered subtitles, moving accent bars, image pan/zoom and fades. Screen recordings keep their full framing. Set project `motion` or a scene's `motion` to a named preset; `none` disables the animated primitives. Add or tune presets in `settings.json` → `motion_presets` without changing Python. Imported MP4/WebM animations can also be scene media, so externally produced designs use the same narration/caption/export workflow.

Sound uses quiet noise-based whooshes and clicks, with optional non-musical ambience. There is no music generator or music bed. A scene's `effect` may be `auto`, `whoosh`, `click` or `none`. The default `auto` marks the intro/ending with a whoosh and body sections with a click. Set `sound.enabled` to false for narration only. Mix parameters have one global owner in `settings.json` → `sound`; a project may override them:

```json
"sound": {
  "enabled": true,
  "ambience": "assets/room-tone.wav",
  "non_musical_confirmed": true,
  "asset_request": null,
  "overrides": {"effects_gain_db": -28, "ambience_gain_db": -34}
}
```

Omit ambience or use `null` when it is unnecessary. Confirm that a supplied ambience file contains no music. Ambience loops to the film length; the mix fades and ducks under speech. `Voiceover.wav`, `SoundEffects.wav` and `Soundtrack.wav` are separate editing stems; the XML uses the final soundtrack. Measured levels do not establish subjective sound quality: listen before publishing.

## Missing assets and future extensions

When a scene needs an illustration, add a request. The build uses existing approved local media first, otherwise searches the free Wikimedia Commons API, checks MIME/size/license/creator metadata, fully decodes the download, and saves a verified cache. Example scene fields:

```json
"media": "assets/missing-illustration.jpg",
"asset_request": {
  "library": "commons",
  "kind": "image",
  "query": "clouds sky",
  "title": null,
  "fallback": "error"
}
```

Use `image` or `video`; an explicit Commons `File:...` title selects a particular result. Search results still need editorial review for relevance. All online illustrations receive a visible stock label, including reused cached media, and cannot replace scenes marked `role: "proof"`. Keep real product evidence in owner-supplied recordings. A search cannot manufacture missing features or verified outcomes.

`search-assets` lists candidates and saves `asset-candidates.json`. Audio requests live at `sound.asset_request` and require `kind: "audio"`, a chosen `File:...` title and `non_musical_confirmed: true`; music-related titles/descriptions are rejected. Search metadata cannot prove an audio file is music-free, so audition external ambience before confirming it.

`AssetSources.json`, `SourceInputs.json` and `Attribution.txt` record creator, source, license, modifications and file hashes. Include attribution when sharing films using credited assets. Cache reuse works offline and rechecks the current license/type/host policy. Set `online.enabled` false to stop new downloads. The default is to stop when requested assets are unavailable; explicit `fallback: "card"` produces an honestly labelled unavailable-illustration card instead. Failed downloads/runs are preserved.

New motion styles and named film formats are data changes. New compatible MediaWiki libraries can be configured with a free-cost declaration, public HTTPS API, allowed hosts and license policy. A different provider API needs a reviewed adapter in `asset_library.py`'s driver registry. New animation tools can supply rendered MP4/WebM clips. The engine does not autonomously install GitHub code, subscribe to services, or claim to understand every future file format.

Motion research used the [GSAP showcase](https://gsap.com/showcase/) and [GSAP repository](https://github.com/greensock/GSAP), [Motion examples](https://motion.dev/examples) and [Motion repository](https://github.com/motiondivision/motion), and [Remotion repository](https://github.com/remotion-dev/remotion) with its [transition documentation](https://www.remotion.dev/docs/transitions). These informed easing, staggering and reusable scene timing. The implementation uses the existing FFmpeg runtime; no library code or premium examples were copied.

## Male voice and expressive delivery

The default voice is **am_michael**, a documented American English male stock voice. The approved alternatives are `am_fenrir`, `am_puck` and British English `bm_george`. Both project configuration and engine voice inventory are checked before synthesis; female and unknown voices are rejected.

| Preset | Direction |
|---|---|
| confident | Steady pacing with measured pauses |
| warm | Slower, more space between phrases |
| energetic | Faster pacing and shorter pauses |
| thoughtful | Slower delivery with longer pauses |

Set the project `delivery`; a scene with `delivery: null` inherits it, while an explicit scene preset overrides it. Preset speed and pause values are maintained in `settings.json`. Write punctuation and phrasing deliberately, and use `pronunciation` for technical terms. Stock voice selection and pacing can shape the delivery; the engine does not expose an emotion-prompt parameter. These presets do not guarantee a particular emotional performance. No voice cloning is used.

## Exports and editing

Each successful build contains:

- `Film-Captioned.mp4` and `Film-Clean.mp4`: H264/AAC at 30fps; portrait shorts and widescreen long films by default.
- `Voiceover.wav`, `Captions.srt`, `Captions.ass` and `Transcript.txt`.
- `media/`: separate scene picture and narration files.
- `Timeline.xml`: Final Cut Pro7 XML for timeline interchange, including the stereo soundtrack when sound is enabled.
- `storyboard.json`, input snapshots, timing, source/attribution records, sound design and `Verification.json` with measured loudness/peak, stem durations, original-source hashes and media checks.

Import `Timeline.xml` into DaVinci Resolve using **File → Import → Timeline**, then import the SRT subtitle track. Alternatively, import the ordered `media/*.mp4`, voice WAV and SRT into CapCut. XML structure and local media links are checked; actual import into an installed editor remains unverified. Generated XML contains local paths: refresh them with the `timeline` command after moving an export. Share MP4/SRT/transcript for public viewing, not private working folders.

## Command line

From WSL, enter this workspace and run:

```bash
python3 studio.py doctor
python3.12 studio.py new my-next-project --format short
python3.12 studio.py new my-long-project --format long
python3.12 studio.py plan my-next-project
python3.12 studio.py search-assets my-next-project image "clouds sky"
python3 studio.py build my-next-project
python3 studio.py verify my-next-project
python3 studio.py timeline my-next-project
python3 studio.py preview
```

The menu runs these same operations. Python 3.12 and WSL are required for the copied local runtime. `machine.local.json` records the actual FFmpeg/ffprobe and TTF font paths on this workstation. Copy `machine.example.json` and configure the installed paths when setting up another machine; `.runtime/` contains Linux Python 3.12 packages and stock model/voice assets, so moving to a different operating system or Python version requires compatible packages. No application environment variables or API keys are used.

## Verification and privacy

Automated policy checks live in `tests/`. Run `python3 -m unittest discover -s tests -v`; use Ruff, mypy, Bandit, gitleaks and the workstation security hook for changes. Python compilation is the build gate for this CLI. A real voice/render/export verification is required alongside the unit tests. The installed pre-commit configuration uses the owner's existing Windows security tools; the public repository includes security and regression workflows.

Keep `.runtime/`, projects, machine configuration, credentials, dossier and memory out of Git. Authenticated raw recordings, browser profiles, cookies and credentials are not part of this shared setup. Inspect each recording for private information before adding it, and represent pending integrations and test payments accurately. Human listening and installed-editor import remain explicit verification limits until exercised.

Official references: [Kokoro engine](https://github.com/thewh1teagle/kokoro-onnx), [stock voice inventory](https://huggingface.co/hexgrad/Kokoro-82M/blob/main/VOICES.md), [FFmpeg filters](https://ffmpeg.org/ffmpeg-filters.html), [WSL command reference](https://learn.microsoft.com/windows/wsl/basic-commands).

## Editorial motion boards

An optional `projects/<name>/motion-board.json` adds original animated diagrams,
kinetic typography, alternating compositions and credited product images to a
conceptual film. Existing projects without this file retain their prior behavior.
Use an operator-authored motion board as the input. Narration remains in
`film.json`; visual copy, colors, branding, image sources and a 1–2 second beat
target belong to the board. This illustration mode rejects real-proof scenes and
existing scene recordings rather than replacing evidence.

The board requires `beat_seconds`, `render_scale`, `brand`, `kicker`,
`illustration_label`, `headline_size`, `headline_minimum`, a validated full-palette `theme`, an `images` object and `scenes` keyed by
film scene ID. Every scene has `chapter` and `beats`; every beat supplies `kind`,
`headline`, `detail`, `source` and 2–4 `labels`. An optional `image` references a
contained project PNG/JPG. Its `images` entry must record a public HTTPS `url`,
`credit` and honest `usage` context. Company copyright is retained; a source URL
does not establish an open licence or grant permission.

Composition names: `car`, `glasses`, `flow`, `chip`, `workspace`, `orbit`, `checks`,
`compare`, `type`. Native graphics are illustrative, not a reconstruction of a
manufacturer's undisclosed engineering. Text/container limits, image containment,
beat coverage and a streaming encoder watchdog guard the flow. Too many authored
beats for the one-second minimum fail explicitly. Source hashes include the board,
product images and generated clips; `EditorialAttribution.json`, `Attribution.txt`
and `MotionBeats.json` travel with the editing export. Verification checks exact
frame coverage and 1–2 second cadence. Pillow 13.0.0 is the pinned local dependency.

