"""One configuration boundary for paths, limits, content and optional local AI."""

import json
import os
import shutil
from dataclasses import dataclass
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
ENVIRONMENT_KEYS = frozenset(
    {
        "STUDIO_DATA",
        "STUDIO_FFMPEG",
        "STUDIO_FFPROBE",
        "STUDIO_FONT",
        "STUDIO_MODEL",
        "STUDIO_VOICES",
        "STUDIO_RUNTIME",
        "STUDIO_ACCOUNTS",
        "STUDIO_AI_URL",
        "STUDIO_AI_MODEL",
        "STUDIO_AI_CURL",
        "STUDIO_BLENDER",
        "STUDIO_TRANSCRIPTION_MODEL",
        "STUDIO_MATTING_MODEL",
    }
)


@dataclass(frozen=True)
class Settings:
    root: Path
    data: Path
    config: dict
    tokens: dict[str, str]
    ffmpeg: str | None
    ffprobe: str | None
    font: Path
    model: Path | None
    voices: Path | None
    runtime: Path | None

    @classmethod
    def load(cls, require_auth=False):
        machine = ROOT / "machine.v2.local.json"
        if machine.is_file():
            for key, value in json.loads(machine.read_text()).items():
                if key not in ENVIRONMENT_KEYS or not isinstance(value, str):
                    raise ValueError("Machine settings must be STUDIO_ string values")
                os.environ.setdefault(key, value)
        config = json.loads((ROOT / "studio-v2.json").read_text())
        tokens = json.loads(os.environ.get("STUDIO_ACCOUNTS", "{}"))
        if not isinstance(tokens, dict) or (require_auth and not tokens):
            raise ValueError(
                "Set STUDIO_ACCOUNTS to an account-to-random-token JSON object"
            )
        if any(not isinstance(v, str) or len(v) < 32 for v in tokens.values()):
            raise ValueError("Account tokens must have at least 32 characters")
        if any(not isinstance(k, str) or not k or len(k) > 80 for k in tokens):
            raise ValueError("Invalid account name")
        if len(set(tokens.values())) != len(tokens):
            raise ValueError("Accounts must have distinct credentials")

        def optional(name):
            return Path(os.environ[name]).resolve() if os.environ.get(name) else None

        return cls(
            ROOT,
            Path(
                os.environ.get("STUDIO_DATA", config["storage"]["directory"])
            ).resolve(),
            config,
            tokens,
            os.environ.get("STUDIO_FFMPEG") or shutil.which("ffmpeg"),
            os.environ.get("STUDIO_FFPROBE") or shutil.which("ffprobe"),
            Path(os.environ.get("STUDIO_FONT", config["render"]["font"])).resolve(),
            optional("STUDIO_MODEL"),
            optional("STUDIO_VOICES"),
            optional("STUDIO_RUNTIME"),
        )

    def contained(self, *parts: str) -> Path:
        path = self.data.joinpath(*parts).resolve()
        if not path.is_relative_to(self.data):
            raise ValueError("Storage path escaped its root")
        return path
