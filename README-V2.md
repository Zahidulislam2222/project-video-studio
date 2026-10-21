# Project Video Studio v2

A local production engine for regular project videos, recorded workflows, technical explanations and short-form edits. It keeps your sources, narration, captions, graphics and render evidence together. AI planning and transcription run through configured local models; there is no paid fallback.

Double-click **Start Video Studio v2.cmd**, choose **10 — Create a video from your inputs**, then supply a script, recording or brief. Optional footage and a second view are placed automatically. Landscape uses side-by-side views; portrait uses upper/lower views. Choose picture-in-picture or custom rectangles in the editable project for other compositions.

The workflow creates narration or draft transcription, a readable storyboard, three composed style frames and a composed animation sample. Review those checkpoints, then build the final film. Generated narration uses approved male stock voices. Recorded speech stays your recording. No music is added; optional synthesized clicks and whooshes have a separate effects stem.

## Local setup

The installed workstation uses WSL Python 3.12 and native Windows FFmpeg. The v1 launcher and films remain separate. A clean Linux x86_64/Python 3.12 installation can install the exact tested package artifacts:

```bash
python3 -m pip install --require-hashes --target .runtime/v2 -r requirements-v2.lock
```

Copy `machine.v2.example.json` to the ignored `machine.v2.local.json` and set executable, font, model and storage paths. Paths must be accessible from WSL; native Windows executables use `/mnt/<drive>/...`. The offline narration model/voice hashes are owned by `settings.json`; model files are separately licensed and excluded from source control. The installed transcription model has a pinned source revision and `ModelIntegrity.json` checksums. Follow [the exact optional model setup](docs/models.md), including the public ASR manifest; obtain model assets from their original publishers; the application never downloads or executes arbitrary model code during production.

`studio-v2.json` owns render dimensions, frame rate, budgets, themes, approved voices, prompts and limits. Machine configuration owns environment-specific paths and the optional installed Ollama model. No cloud account is needed. External integrations remain optional.

## Commands

Run commands from this project folder in WSL:

```bash
python3 -m studio_v2 doctor
python3 -m studio_v2 menu
python3 -m studio_v2 prepare request.json workspace/productions/my-film
python3 -m studio_v2 plan workspace/productions/my-film/project.json
python3 -m studio_v2 style-test workspace/productions/my-film/project.json workspace/previews/my-style
python3 -m studio_v2 animation-test workspace/productions/my-film/project.json workspace/previews/my-motion
python3 -m studio_v2 build workspace/productions/my-film/project.json
python3 -m studio_v2 jobs
python3 -m studio_v2 cancel JOB_ID
python3 -m studio_v2 build revised-project.json --resume JOB_ID
python3 -m studio_v2 help 'How do captions work?'
```

For a script, a request can contain:

```json
{"title":"My project workflow","script_file":"script.txt","ratio":"portrait","style":"technical","footage":[],"effects":false}
```

For recorded speech, use `recording` plus optional `captions_file` and `language`. Without SRT, the configured local transcription model drafts captions. For supplied media, set `media_approved: true` only after checking rights and private information. `footage` accepts approved image/video paths in order; `companion` supplies a second view. Relative paths resolve beside the request. The script is spoken as supplied; a brief with `use_ai: true` asks the local director to propose narration instead. AI output and technical names need review.

Short and long films use the same versioned project contract. There is no requirement to squeeze narration into a fixed preset length. The editing envelope permits up to two hours; that is a validation limit, not a performance measurement. Split large productions into manageable chapters and retain successful packages.

## Reference and revision workflow

```bash
python3 -m studio_v2 analyze reference.mp4 workspace/references/my-reference
python3 -m studio_v2 profile workspace/profiles/my-look image1.png image2.png --notes 'Describe typography, texture and motion direction'
python3 -m studio_v2 revise project.json changes.json revised-project.json
```

Local video analysis measures cuts, shot lengths, palette and sampled framing. Camera moves, typography and musical beat interpretation need editorial review. Profile training extracts a readable palette and retains your art-direction notes and source hashes; it does not learn an entire animation language from pictures. Apply the profile through a production request's `profile` field. Inspect consistent references before approving a style. Online video links can be used during assisted reference research; the local analyzer requires an approved local video file.

A revision file accepts project fields, stable shot IDs, or timestamps in an audio-prepared project:

```json
{"shots":{"shot-02":{"layout":"picture-in-picture"}},"at":[{"seconds":42,"set":{"title":"Corrected explanation"}}]}
```

Resume creates a new export and reuses completed shots only when source bytes, shot inputs, configuration, relevant dependencies and tool/model/font hashes match. Earlier revisions and failed exports remain. One renderer operates per workspace. Ctrl+C or `cancel` stops active work; a failed run never advances `latest-export.json`.

## Composition and finishing

For a human presenter, the guided workflow can generate a local cutout. Choose a video `companion` (or a video `recording` with no separate main footage), enable `matte_presenter`, and inspect the composed animation checkpoint. The pinned RVM ONNX model runs on CPU, with four recurrent states carried between frames. Configure `STUDIO_MATTING_MODEL`; the model hash and processing limits are in `studio-v2.json`. The upstream repository identifies [GPL-3.0 for its code](https://github.com/PeterL1n/RobustVideoMatting/blob/master/LICENSE); verify the exact optional model release terms separately before redistributing weights.

```bash
python3 -m studio_v2 matte presenter.mp4 workspace/cutouts/my-shot --start 0 --seconds 8
```

Cutouts retain synchronized lossless `Foreground.mkv` and grayscale `Mask.mkv`, sampled masks and a verification report. Prepared projects preserve the original source in portable exports and label the AI treatment. Callout depth0 puts text behind the presenter; depth4 puts it in front. Human cutouts cannot be marked as unaltered proof. Processing is bounded to30 seconds per shot,1,280 pixels on the long edge, two CPU threads and a30 minute deadline; split longer shots. Generated media has a separate8 GiB per-file bound within the existing10 GiB account-asset budget. Failed intermediates remain; successful scratch frames are reclaimed. Inspect hair, hands, blur and occlusions: an alpha mask is not an editorial quality guarantee. Natural talking-head footage still needs representative review.

Shots support multiple image/video layers, opacity, grayscale image/video masks, matching trims, contain/cover fitting, camera push/pull on stills, ordered callouts, semantic beats, diagram motion and incoming cut/fade/slide transitions. Masked sources require pre-authored camera movement. Genuine proof needs supplied source media and a source note; illustrative graphics remain illustrative. Source notes render above footage in a bounded contrast-backed region; shorten a note if it cannot fit legibly. Missing footage is rejected instead of silently repeated. Typography rejects content that cannot fit at the supported minimum size.

Exports include clean/captioned MP4 masters when captions are available, SRT, transcript, voiceover, optional effects/mix stems, normalized master audio, storyboard, source hashes, portable `Inputs`, project JSON, XML timeline and verification reports. Final checks include frame count, dimensions, full decoding and measured loudness/true peak. Phrase timing from generated speech and word timing from recognized speech have different accuracy limits.

Import `Timeline.xml` into an editor that supports Final Cut Pro XML and import `Captions.srt` separately. Picture clips contain baked graphics. Text, masks, sources and layouts remain editable in the source project; rerender to apply changes. Blender scenes also retain native `.blend` sources. This does not claim layered native After Effects, Premiere or Resolve graphics round-tripping.

```bash
python3 -m studio_v2 restore exported-package restored-project.json
python3 -m studio_v2 blender workspace/scenes/my-scene --labels Capture Edit Review --seconds 4 --transparent
```

Blender's transparent output uses ProRes 4444 MOV; opaque output uses H.264 MP4. Keep the `.blend` and original frames for native editing. Resolve external scripting depends on the installed edition/settings; the adapter must connect and import successfully before it is treated as verified. OBS capture control is currently disabled in the workstation's OBS settings. CapCut can receive MP4/audio/SRT files; native project automation is not claimed. StykAnimate exports can be imported as ordinary approved media; its application code is not bundled.

## Verification and scope

```bash
PYTHONPATH=.runtime/v2 python3 -m unittest discover -s tests -q
ruff check .
mypy studio_v2 --ignore-missing-imports --check-untyped-defs
bandit -r studio_v2 -ll
```

See `CORE-ACCEPTANCE.md` and the per-export reports for measured evidence. Review representative final frames, the entire audio, source privacy and factual claims before publishing. Automated checks do not judge a creator's taste. The seven procedural visual presets are configurable starting points; they do not promise identical creator styles or seven complete illustration engines.

The active release scope is local video production. Hosted frontend/backend services, cloud deployment and measured service-level objectives remain future work; no capacity or uptime result is inferred from local rendering.
