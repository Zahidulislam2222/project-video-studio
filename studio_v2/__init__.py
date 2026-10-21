"""Project Video Studio: local production workspace."""

import json
import sys
from pathlib import Path

_root = Path(__file__).resolve().parent.parent
_config = _root / "studio-v2.json"
if _config.is_file():
    _packages = (_root / json.loads(_config.read_text())["runtime_packages"]).resolve()
    if not _packages.is_relative_to(_root):
        raise ValueError("Runtime package directory escaped the Studio")
    if _packages.is_dir():
        sys.path.insert(0, str(_packages))
