Place HIPE 2026 input JSONL files in this directory.

The baseline now works directly with the cloned `HIPE-2026-data/` repository at the
project root instead of copying files into this directory.

The default `make install-data` target clones the official GitHub repo into:

- `HIPE-2026-data/`

Example:

- `HIPE-2026-data/data/newspapers/v1.0/HIPE-2026-v1.0-impresso-train-en.jsonl`
- `HIPE-2026-data/data/newspapers/v1.0/HIPE-2026-v1.0-impresso-train-de.jsonl`
- `HIPE-2026-data/data/newspapers/v1.0/HIPE-2026-v1.0-impresso-train-fr.jsonl`
