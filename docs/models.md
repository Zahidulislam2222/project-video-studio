# Optional local model assets

No weights are included in Git. Download only the components you intend to use, review their upstream licenses, and validate hashes before production. These are free local inference paths; no cloud API is configured. Run from the repository root with the hash-locked runtime on PYTHONPATH.

## Narration

The tested files come from the original [kokoro-onnx model-files-v1.1 release](https://github.com/thewh1teagle/kokoro-onnx/releases/tag/model-files-v1.1):

```bash
mkdir -p .runtime/models
curl -fL https://github.com/thewh1teagle/kokoro-onnx/releases/download/model-files-v1.1/kokoro-v1.0.int8.onnx -o .runtime/models/kokoro-v1.0.int8.onnx
curl -fL https://github.com/thewh1teagle/kokoro-onnx/releases/download/model-files-v1.1/voices-v1.0.bin -o .runtime/models/voices-v1.0.bin
python3 - <<'PYVERIFY'
import hashlib, json
from pathlib import Path
cfg = json.loads(Path('settings.json').read_text())
for key in ('model', 'voices'):
    path = Path(cfg[key])
    assert hashlib.sha256(path.read_bytes()).hexdigest() == cfg[key + '_sha256'], path.name
print('Narration assets verified')
PYVERIFY
```

Set STUDIO_MODEL and STUDIO_VOICES in ignored machine configuration to the absolute paths of these files. Set STUDIO_RUNTIME to the installed .runtime/v2 package directory. The original model/voice notices remain separate from the source-code license.

## English transcription

The tested repository/revision and file inventory are in [the public transcription manifest](models/transcription-base-en.json); every exact hash is published in the standard [SHA256SUMS file](models/transcription-base-en.sha256). Download its small allowlist at that exact revision, validate every file, then write the required local ModelIntegrity.json:

```bash
python3 - <<'PYVERIFY'
import hashlib, json
from pathlib import Path
from huggingface_hub import snapshot_download
manifest = json.loads(Path('docs/models/transcription-base-en.json').read_text())
checksums = {}
for line in Path('docs/models', manifest['checksum_file']).read_text().splitlines():
    value, name = line.split(maxsplit=1)
    checksums[name] = value
if set(checksums) != set(manifest['files']):
    raise ValueError('Model inventory and checksum list differ')
folder = Path('.runtime/models/transcription-base-en')
snapshot_download(repo_id=manifest['repository'], revision=manifest['revision'],
                  local_dir=folder, allow_patterns=manifest['files'])
for name, expected in checksums.items():
    path = folder / name
    assert hashlib.sha256(path.read_bytes()).hexdigest() == expected, name
manifest['files'] = checksums
(folder / 'ModelIntegrity.json').write_text(json.dumps(manifest, indent=2))
print('English transcription assets verified')
PYVERIFY
```

Set STUDIO_TRANSCRIPTION_MODEL to that absolute directory. This English model produces draft speech recognition; review names and technical terminology. Corrected SRT can be supplied instead. Runtime recognition uses local files only and validates the manifest again.

## Human matting

The exact tested [RVM v1.0.0 ONNX file](https://github.com/PeterL1n/RobustVideoMatting/releases/tag/v1.0.0) is configured in studio-v2.json under matting.model_source/model_sha256. Download the original publisher's rvm_mobilenetv3_fp32.onnx into an ignored model directory and compare SHA256 to that maintained configuration value. Set STUDIO_MATTING_MODEL to its absolute path. The doctor/worker reject a mismatch.

The upstream repository identifies GPL-3.0 for code. Verify the particular model release's redistribution terms separately; no weights are bundled or relicensed here. Preview natural footage for hair, blur and occlusion quality.

## AI planning

Install a supported local Ollama application/model separately. Configure its loopback URL and installed model name through STUDIO_AI_URL/STUDIO_AI_MODEL; there is no paid fallback. Model choice and hardware need separate quality/latency evaluation. Blender likewise uses its separately configured installed executable.
