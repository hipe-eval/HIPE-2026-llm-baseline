"""Export helpers for scorer-compatible JSONL and debug traces."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from .io_hipe import HipeDocument, write_jsonl


def write_submission_jsonl(documents: list[HipeDocument], path: str | Path) -> None:
    write_jsonl(documents, path)


def initialize_debug_jsonl(path: str | Path) -> None:
    Path(path).write_text("", encoding="utf-8")


def append_debug_jsonl_record(record: dict[str, Any], path: str | Path) -> None:
    with Path(path).open("a", encoding="utf-8") as handle:
        handle.write(json.dumps(record, ensure_ascii=False))
        handle.write("\n")


def write_debug_jsonl(records: list[dict[str, Any]], path: str | Path) -> None:
    with Path(path).open("w", encoding="utf-8") as handle:
        for record in records:
            handle.write(json.dumps(record, ensure_ascii=False))
            handle.write("\n")
