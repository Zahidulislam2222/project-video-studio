# Video production rebuild acceptance

The active release scope is the local production engine. Publishing, hosted user
interfaces and growth documentation follow after the core workflow is verified.

1. Keep every previous film and original v1 source byte-identical.
2. Validate project/shot/layer contracts, genuine source hashes and safe paths.
3. Produce clean and captioned portrait and landscape films with male narration,
   exact phrase timing, authored recorded-audio cues and separate audio stems.
4. Exercise side-by-side, upper/lower, picture-in-picture, image/video layers,
   opacity, masks, animated diagrams, typography, callouts and transitions.
5. Analyze a reference into measured cuts, duration, palette and a contact sheet;
   retain limitations for camera, typography and beat analysis.
6. Render three style frames and an animation test before full production.
7. Exercise a real Blender shot and preserve its editable source. Verify each
   installed editor/capture integration before claiming that integration works.
8. Preserve failed runs, stop child processes on cancellation, resume compatible
   completed shots, and invalidate caches after input/settings/tool changes.
9. Verify real short and long films through full decoding, frame/audio inspection,
   source hashes, caption timing, editing-package links and fresh-context review.
10. Provide an understandable local launcher and operator instructions, with
    unavailable gates and capabilities explicitly recorded before release.

## Local verification status — 2026-10-21

| Requirement | Status | Evidence and limits |
|---|---|---|
| 1. Preserve previous work | Verified | 1,641 historical files independently SHA256-matched; original v1 code retained. Ignore rules extended for private v2 files. |
| 2. Contracts and source boundaries | Verified | Closed models, source hashes, owner isolation, revision conflicts and package symlink guards exercised. Source ownership/rights still require the operator's review. |
| 3. Narration, captions and stems | Verified | Portrait70.733s/2,122frames/24 cues and landscape307.133s/9,214frames/108 cues; clean/captioned masters fully decode; local generated/recorded narration paths exercised. |
| 4. Composition | Verified | Masks, opacity, depth callouts, ratios, diagrams, transitions and layers exercised; actual-frame review corrected caption/label sizing. A later focused60-frame PiP check verifies foreground source notes. |
| 5. Reference measurements | Verified | Local reference cut/palette/contact-sheet flow executed. Full style/camera/beat understanding remains outside this measurement claim. |
| 6. Checkpoints | Verified | Three actual composed style frames and animation previews executed; narration-prepared storyboards retained. |
| 7a. Blender | Verified | Native Blender rendered editable scene, frames, opaque MP4 and transparent ProRes4444MOV. |
| 7b. Other native integrations | Unverified | Resolve external API did not connect; OBS control was disabled; CapCut/native layered-editor automation was not executed. Owner/workstation integration work required before claiming support. |
| 8. Recovery | Verified | Actual CLI cancellation/concurrent-render rejection; preserved runs/latest-success pointer; hash-bound resume and restoration regressions pass. |
| 9a. Media verification | Verified | Real short/long decode, dimensions, frame counts, measured audio, source copies, XML link existence and independent sampled-frame review. XML validity/links do not prove native import. |
| 9b. Listening/native round trip | Unverified | Owner must listen to each finished film. Installed editor round trips remain unverified. |
| 10. Local handoff | Verified | Windows launcher/menu/doctor/exit; exact isolated runtime parity; local operator guide;90tests,types,lint and recorded security gates pass. |

This verifies the listed local workflows. It does not mark the whole researched
creative vision complete. Automatic full reference-style reconstruction,
seven independent illustration engines, native
layered graphics round trips and multi-agent shot/reviewer orchestration remain
unfinished. These are outstanding core capabilities, not completed work hidden
behind the deferred frontend/publication scope.

The full-length validation films were retained before the last source-note
foreground correction. The installed correction is covered by a focused actual
PiP render and a pixel regression; earlier artifacts remain unchanged. Human
judgment, listening and source/licensing review still apply to real films.

## Focused creative upgrade — local human cutouts

Automatic human video matting is implemented with a separately configured,
hash-pinned local ONNX model. Six additional checks exercise timing/contracts,
model tampering, input/derived/account quotas, worker isolation, guided cutout
preparation, media decoding and portable original-source restoration. An actual
60-frame composition places text behind and in front of an animated NASA
public-domain portrait. Actual worker cancellation/deadline tests preserve partial
work, stop the worker and release its lock. This establishes the local processing
and composition paths; natural talking-head hair/motion/occlusion quality remains
unverified until representative footage is reviewed. The broader researched
creative capabilities listed above remain open.

Installed validation after this upgrade:90/90tests pass;26 v2 modules type-check;
whole-source lint,medium/high Bandit and the configured Gitleaks/Bandit hook pass.
Semgrep runs200applicable rules on 28 v2/test targets with0findings. Fresh review
found no blocking defect in this focused scope.

## Source publication checks — 21 October 2026

After the earlier core snapshot, legacy process/download helpers gained whole-operation deadlines, bounded raw TLS downloads and guaranteed process cleanup. Five release-boundary tests were added and the clean-checkout fixtures updated. Current installed suite:95/95 tests passed in27.603seconds; all36 Python modules type-check. Full staged Gitleaks/Bandit/Semgrep and configured fail-closed hook passed. Earlier preservation evidence describes its recorded snapshot; historical film files remain unchanged. Initial public source release is authorized; native-editor, human-listening and broader creative gaps above remain open.
