from __future__ import annotations

import json
import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from hipe2026_mistral_baseline.export import (
    append_debug_jsonl_record,
    initialize_debug_jsonl,
)


class TestExport(unittest.TestCase):
    def test_initialize_and_append_debug_jsonl(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            path = Path(tmpdir) / "debug.jsonl"

            initialize_debug_jsonl(path)
            self.assertEqual(path.read_text(encoding="utf-8"), "")

            append_debug_jsonl_record({"a": 1}, path)
            append_debug_jsonl_record({"b": 2}, path)

            lines = path.read_text(encoding="utf-8").splitlines()
            self.assertEqual([json.loads(line) for line in lines], [{"a": 1}, {"b": 2}])


if __name__ == "__main__":
    unittest.main()
