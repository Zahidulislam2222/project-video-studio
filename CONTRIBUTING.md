# Contributing

Keep changes focused and preserve prior successful/failed exports. Start with README-V2.md and CORE-ACCEPTANCE.md. Configuration/content belongs in maintained JSON/templates; machine paths and secrets stay in ignored local configuration.

For development, create and activate a Python 3.12 virtual environment, install `requirements-dev.txt`, and install the application runtime from the hash lock. Install the maintained gitleaks and Semgrep command-line tools separately. The local hooks require these commands on PATH and fail when a required scanner is unavailable.

```bash
python3 -m pip install -r requirements-dev.txt
pre-commit install
pre-commit run --all-files
PYTHONPATH=.runtime/v2 python3 -m unittest discover -s tests -q
ruff check .
mypy studio_v2
```

Run meaningful affected real-media checks alongside tests, types and security scans. Distinguish model/native-editor checks from ordinary CI. Request fresh review for nontrivial changes, disclose unexecuted gates and update the defect record when a verified behavior fails. Do not disable hooks or add scanner suppressions to make a failing change pass.

Submit a pull request describing the concrete behavior change, verification, source/model assumptions and remaining limits. Keep copyrighted footage, private operational notes and credentials out of issues and pull requests. Code contributions are submitted under the repository GPL-3.0 license; third-party assets require their own provenance/permission.
