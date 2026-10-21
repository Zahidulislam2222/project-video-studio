# Defect log

Record any defect found after a verified release; preserve earlier entries.

| Date | What escaped | Gate that should have caught it | Gate added / resolution |
|---|---|---|---|
| 2026-10-17 | First verified motion export had empty image attribution; streaming timeout and malformed-board cases were missing | Fresh review and source-provenance gate | Watchdog regression, container/text guards, all-authored-beat coverage, hash-bound editorial credits and final visual revision added |
| 2026-10-17 | Visual revision cache omitted global/image/renderer dependencies; partial progress reset; chip labels dropped; provenance fields overrideable | Fresh review and visual/cache regression gates | Partial picture reuse retired; full visual regeneration, all-label probes, restricted metadata keys and JSON palette; final review APPROVE |

## V2 findings caught during pre-release validation — 2026-10-21

These were found before public release; no live customer incident is implied.

| Finding | Missed check | Added gate / resolution |
|---|---|---|
| Default subtitle canvas oversized portrait captions and hid lower media | Codec/metadata checks did not inspect actual frames | Explicit ASS pixel canvas, bounded per-ratio captions, portrait frame review and safe-area regression |
| Companion video restarted at each recorded shot | Single-shot tests missed continuity | Shared recording offsets and independent two-group reproduction |
| Picture-in-picture could cover a source note | Source metadata existed but visible credit was not checked | Foreground contrast-backed notes; actual media pixel assertion and focused PiP export |
| Portable Inputs could resolve through an external symlink | Individual source containment trusted a redirected root | Reject escaped Inputs roots; dedicated symlink regression |
| Generated lossless cutouts shared a smaller ordinary upload cap | First integration tests used only small clips | Separate bounded derived-media cap, retained account quota, restoration-aware imports and size/quota regression |
| Clean-checkout graphic tests depended on ignored workstation configuration | Local tests did not exercise a public checkout | Tests resolve the documented public/configured font with isolated tool fixtures |
| Legacy process/download helpers failed strict publication gates | Earlier local evidence did not cover the complete staged source | Bounded asynchronous process lifecycle, whole-download deadline/raw byte limits and five real boundary regressions; no scanner suppression |
