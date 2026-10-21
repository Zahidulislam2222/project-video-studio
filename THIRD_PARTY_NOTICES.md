# Third-party notices

The root GPL-3.0 license covers original project code. It does not relicense dependencies, models, footage, fonts, editor software or a creator's visual assets.

| Component | Role and terms |
|---|---|
| kokoro-onnx | Optional offline inference engine; MIT upstream license. |
| Kokoro82M and stock voice assets | Separately obtained model/voice assets; upstream model card identifies Apache 2.0. Review the exact downloaded release and voice notices. |
| Robust Video Matting | Optional upstream repository/release identifies GPL-3.0 for code. Verify the particular ONNX release/model redistribution terms separately before distributing weights. No weights are bundled. |
| faster-whisper / CTranslate2 / ONNX Runtime | Optional local recognition/inference packages; retain their installed upstream licenses and verify selected model terms. |
| FFmpeg | External executable; actual build determines LGPL/GPL and codec obligations. Not redistributed here. |
| Blender | External optional renderer, GPL upstream. Its application is not redistributed here. Generated scenes/media need their own source/asset checks. |
| DaVinci Resolve / CapCut / OBS | Optional installed-editor/capture workflows; availability is not evidence of a verified control integration. No proprietary application is bundled. |
| Fonts, stock/reference media | Obtain permission for the intended use; retain credits and source licenses. No reference-video assets or workstation fonts are bundled. |

Official sources: [Kokoro](https://huggingface.co/hexgrad/Kokoro-82M), [kokoro-onnx](https://github.com/thewh1teagle/kokoro-onnx), [RVM](https://github.com/PeterL1n/RobustVideoMatting), [FFmpeg legal](https://ffmpeg.org/legal.html), [Blender license](https://www.blender.org/about/license/). Dependency metadata and its installed notices remain authoritative for each exact package. A generated film needs a separate rights/privacy review.
