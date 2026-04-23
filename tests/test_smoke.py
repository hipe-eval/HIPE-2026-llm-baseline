from __future__ import annotations

import sys
import unittest
from pathlib import Path
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from hipe2026_mistral_baseline.io_hipe import load_jsonl
from hipe2026_mistral_baseline.run_baseline import run_documents


FIXTURE_PATH = Path(__file__).resolve().parent / "fixtures" / "sample_input.jsonl"


class FakeRunner:
    def __init__(self) -> None:
        self._responses = {
            "Nastassia Kinski": '{"person":"Nastassia Kinski","place":"Geneva","at":"TRUE","isAt":"FALSE","evidence":"The text says she stayed in Geneva last year."}',
            "Rudolf Koller": '{"person":"Rudolf Koller","place":"Zurich","at":"TRUE","isAt":"TRUE","evidence":"The text says he works and lives there."}',
            "Victor Hugo": 'not valid json',
        }

    def generate(self, prompt: str) -> str:
        for marker, response in self._responses.items():
            if marker in prompt:
                return response
        raise AssertionError("Unexpected prompt")


class TestSmokePipeline(unittest.TestCase):
    def test_run_documents(self) -> None:
        documents = load_jsonl(FIXTURE_PATH)
        with patch(
            "hipe2026_mistral_baseline.run_baseline.ENABLE_INLINE_PAIR_PROGRESS", False
        ), patch("hipe2026_mistral_baseline.run_baseline.LOGGER.info"):
            output_documents, debug_records = run_documents(
                documents,
                runner=FakeRunner(),
                prompt_template=(
                    "Person mentions: {person_mentions}\n"
                    "Place mentions: {place_mentions}\n"
                    "Text: {article_text}\n"
                    'Return {{"person":"{person_value}","place":"{place_value}","at":"","isAt":"","evidence":""}}'
                ),
            )

        self.assertEqual(len(output_documents), 3)
        self.assertEqual(len(debug_records), 3)

        en_pair = output_documents[0].sampled_pairs[0]
        self.assertEqual(en_pair.at, "TRUE")
        self.assertEqual(en_pair.is_at, "FALSE")

        de_pair = output_documents[1].sampled_pairs[0]
        self.assertEqual(de_pair.at, "TRUE")
        self.assertEqual(de_pair.is_at, "TRUE")

        fr_pair = output_documents[2].sampled_pairs[0]
        self.assertEqual(fr_pair.at, "FALSE")
        self.assertEqual(fr_pair.is_at, "FALSE")
        self.assertTrue(debug_records[2]["used_default"])


if __name__ == "__main__":
    unittest.main()
