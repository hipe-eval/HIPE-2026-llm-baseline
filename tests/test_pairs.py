from __future__ import annotations

import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from hipe2026_mistral_baseline.io_hipe import load_jsonl
from hipe2026_mistral_baseline.pair_generation import build_pair_tasks


FIXTURE_PATH = Path(__file__).resolve().parent / "fixtures" / "sample_input.jsonl"


class TestPairGeneration(unittest.TestCase):
    def test_build_pair_tasks(self) -> None:
        documents = load_jsonl(FIXTURE_PATH)
        tasks = build_pair_tasks(documents[0])
        self.assertEqual(len(tasks), 1)
        self.assertEqual(tasks[0].pair.key(), ("doc-en-1-p1", "doc-en-1-l1"))
        self.assertEqual(tasks[0].publication_date, "1920-08-19")


if __name__ == "__main__":
    unittest.main()
