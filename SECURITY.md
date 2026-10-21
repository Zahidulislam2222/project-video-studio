# Security

This release is local workstation software. It is not a hosted multi-tenant service and does not provide a public account, upload or remote-rendering endpoint.

Use trusted, maintained FFmpeg/Blender/model packages. Treat scripts, reference media, captions and AI output as untrusted input. Check source rights/private content before import; model output cannot verify factual claims. Optional AI planning accepts only a configured loopback endpoint and has no publishing or shell-action tools. No paid fallback is enabled.

The engine validates closed project contracts, source ownership/hashes, contained storage and portable restoration paths. It bounds media/tool operations and preserves failed runs. These controls and scanners do not establish blanket security or legal compliance. Local media and SQLite records are not automatically encrypted; use appropriate disk encryption, operating-system permissions and backups.

Never commit credentials, machine configuration, runtime/models, recordings, private memory or working export packages. Inspect public diffs before pushing. Keep `.env.example` free of real values. A hosted edition would need authenticated per-request authorization, tenant isolation, upload abuse controls, vendor/privacy review and operational validation before release.

For vulnerabilities, use the repository’s GitHub Security → Report a vulnerability control. If it is unavailable, open a minimal issue asking the owner for a private contact channel, without exploit details or private data. Routine bugs may use GitHub Issues. No response-time commitment is currently offered.
