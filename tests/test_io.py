from __future__ import annotations

import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from hipe2026_mistral_baseline.io_hipe import load_jsonl


FIXTURE_PATH = Path(__file__).resolve().parent / "fixtures" / "sample_input.jsonl"


class TestHipeIO(unittest.TestCase):
    def test_load_jsonl(self) -> None:
        documents = load_jsonl(FIXTURE_PATH)
        self.assertEqual(len(documents), 3)
        self.assertEqual(documents[0].document_id, "doc-en-1")
        self.assertEqual(documents[1].language, "de")
        self.assertEqual(documents[2].sampled_pairs[0].place_value, "Paris")


if __name__ == "__main__":
    unittest.main()
