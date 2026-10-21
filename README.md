# Project Video Studio

Local video production for project walkthroughs, technical explanations, shorts and longer films. Python orchestration, FFmpeg composition, offline narration/transcription and optional local AI planning keep production on your workstation.

**Author: Zahidul Islam.** Current release scope: a local production engine. The broader creative rebuild continues; hosted frontend/backend services are not included.

## Start here

On the configured Windows/WSL workstation, open **Start Video Studio v2.cmd** and choose **10 — Create a video from your inputs**. On Linux/WSL, run `python3 -m studio_v2 menu` after setup. Supply a script, recording or brief, review the storyboard/style/animation checkpoints, then build.

- [Setup, commands and production guide](README-V2.md)
- [Verified capabilities and remaining work](CORE-ACCEPTANCE.md)
- [Technical overview, before/after and roadmap](docs/technical-overview.md)
- [Retained v1 workflow](docs/legacy-workflow.md)

## What works locally

- Script/recording preparation, approved male narration, local speech-recognition drafts and optional loopback Ollama storyboarding.
- Portrait upper/lower, landscape side-by-side, picture-in-picture and explicit layered compositions.
- Motion graphics, callouts in front of/behind subjects, supplied masks and local automatic human matting.
- Reference cut/palette/contact-sheet measurements, reusable image palettes, three composed style frames and animation checkpoints.
- Original Blender scenes with editable `.blend`, opaque MP4 or transparent ProRes4444 output.
- Captioned/clean exports, separate audio stems, normalization, full decoding/frame/hash checks, portable originals and focused revisions.
- Preserved failed runs, cancellation, bounded processing, one renderer per workspace and dependency-bound resume.

Seven procedural presets are starting points, not seven complete illustration engines. Full reference-style reconstruction, autonomous shot/reviewer orchestration and native layered editor round trips remain unfinished. Natural talking-head matting needs representative hair/motion/occlusion review. XML contains baked picture clips; native editor import and human listening remain separate checks.

## Clean setup

Use Linux x86_64/WSL with Python 3.12, FFmpeg/ffprobe and a licensed TrueType font. Install the runtime into the ignored folder:

```bash
python3 -m pip install --require-hashes --target .runtime/v2 -r requirements-v2.lock
export PYTHONPATH="$PWD/.runtime/v2${PYTHONPATH:+:$PYTHONPATH}"
cp machine.v2.example.json machine.v2.local.json
python3 -m studio_v2 doctor
python3 -m studio_v2 menu
```

Configure your local tool/font/runtime/model paths in `machine.v2.local.json`. Follow [the exact optional model setup](docs/models.md), with original release URLs and the public transcription file manifest. Narration, transcription, AI planning, matting and Blender each require their corresponding local assets/tools. No models, recordings, fonts, proprietary editors or copied runtime packages are distributed here. The hash lock targets the tested platform; other platforms need separate validation.

## Verification

The configured workstation passed 95 tests,36 Python module type checks, whole-source lint, medium/high Bandit, configured Gitleaks/Bandit hooks and 200 applicable Semgrep rules on 28 v2/test targets. Dependency audit found no known advisories in the checked 39-package runtime at that check; this is not a perpetual security guarantee. Actual short 70.733 s and long 307.133 s films passed recorded media checks; later fixes have focused regression/render evidence. These are local measurements, not public-service load or uptime evidence.

```bash
PYTHONPATH=.runtime/v2 python3 -m unittest discover -s tests -q
python3 -m compileall -q studio_v2
```

Optional model/native-editor checks can skip when their prerequisites are not configured. CI reports its own executed scope; it does not reproduce the workstation's natural-footage or native-editor review.

## Contributing and security

See [CONTRIBUTING.md](CONTRIBUTING.md), [SECURITY.md](SECURITY.md) and [DEFECT-LOG.md](DEFECT-LOG.md). GitHub workflows use standard public Linux runners, read-only source permissions and no paid inference. No deployment, artifact hosting or billing activation is configured.

## License and assets

Original project code is licensed under [GPL-3.0](LICENSE), copyright 2026 Zahidul Islam. Third-party packages, optional models, media and editors retain their own terms; see [THIRD_PARTY_NOTICES.md](THIRD_PARTY_NOTICES.md) and [VOICE-LICENSE.txt](VOICE-LICENSE.txt). A reference URL does not grant reuse rights. Keep recordings, secrets, models, machine settings and working exports outside Git.
