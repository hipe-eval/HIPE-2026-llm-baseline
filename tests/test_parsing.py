from __future__ import annotations

import sys
import unittest
from dataclasses import replace
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from hipe2026_mistral_baseline.parsing import ParseError, parse_model_response
from hipe2026_mistral_baseline.io_hipe import load_jsonl
from hipe2026_mistral_baseline.pair_generation import build_pair_tasks
from hipe2026_mistral_baseline.validation import validate_prediction


FIXTURE_PATH = Path(__file__).resolve().parent / "fixtures" / "sample_input.jsonl"


class TestParsing(unittest.TestCase):
    def test_parse_fenced_json(self) -> None:
        raw = """```json
        {
          "person": "Victor Hugo",
          "place": "Paris",
          "at_explanation": "The article says he stayed in Paris.",
          "at": "TRUE",
          "isAt_explanation": "The article does not place him there in the immediate present.",
          "isAt": "FALSE",
        }
        ```"""
        parsed = parse_model_response(raw)
        self.assertEqual(parsed.person, "Victor Hugo")
        self.assertEqual(parsed.place, "Paris")
        self.assertEqual(parsed.at_explanation, "The article says he stayed in Paris.")
        self.assertEqual(parsed.at, "TRUE")
        self.assertEqual(
            parsed.is_at_explanation,
            "The article does not place him there in the immediate present.",
        )
        self.assertEqual(parsed.is_at, "FALSE")

    def test_parse_trailing_comma(self) -> None:
        raw = """
        {
          "person": "Rudolf Koller",
          "place": "Zurich",
          "at": "PROBABLE",
          "isAt": "FALSE",
        }
        """
        parsed = parse_model_response(raw)
        self.assertEqual(parsed.at, "PROBABLE")

    def test_missing_field_raises(self) -> None:
        with self.assertRaises(ParseError):
            parse_model_response('{"person":"x","place":"y","at":"TRUE"}')

    def test_validation_truncates_long_evidence(self) -> None:
        document = load_jsonl(FIXTURE_PATH)[0]
        task = build_pair_tasks(document)[0]
        long_evidence = " ".join(f"word{i}" for i in range(120))
        parsed = parse_model_response(
            (
                '{"person":"Nastassia Kinski","place":"Geneva",'
                f'"at_explanation":"{long_evidence}","at":"TRUE",'
                f'"isAt_explanation":"{long_evidence}","isAt":"FALSE"'
                "}"
            )
        )
        validated = validate_prediction(task, parsed)
        self.assertIsNotNone(validated.at_explanation)
        self.assertIsNotNone(validated.is_at_explanation)
        assert validated.at_explanation is not None
        assert validated.is_at_explanation is not None
        self.assertLessEqual(len(validated.at_explanation.split()), 100)
        self.assertLessEqual(len(validated.is_at_explanation.split()), 100)
        self.assertTrue(validated.at_explanation.endswith("..."))
        self.assertTrue(validated.is_at_explanation.endswith("..."))

    def test_validation_canonicalizes_isat_true_to_at_true(self) -> None:
        document = load_jsonl(FIXTURE_PATH)[0]
        task = build_pair_tasks(document)[0]
        parsed = parse_model_response(
            '{"person":"Nastassia Kinski","place":"Geneva","at_explanation":"The article places her there now.","at":"FALSE","isAt_explanation":"The article places her there now.","isAt":"TRUE"}'
        )
        validated = validate_prediction(task, parsed)
        self.assertEqual(validated.at, "TRUE")
        self.assertEqual(validated.is_at, "TRUE")

    def test_validation_matches_escaped_linebreak_mentions(self) -> None:
        document = load_jsonl(FIXTURE_PATH)[0]
        task = build_pair_tasks(document)[0]
        task = replace(
            task,
            pair=replace(
                task.pair,
                pers_mentions_list=["größten\\nAußenminister Deleass.", "Delcass."],
                loc_mentions_list=["Vatikan"],
            ),
        )
        parsed = parse_model_response(
            '{"person":"größten\\nAußenminister Deleass.","place":"Vatikan","at_explanation":"OCR mention matched.","at":"TRUE","isAt_explanation":"OCR mention matched.","isAt":"FALSE"}'
        )
        validated = validate_prediction(task, parsed)
        self.assertEqual(validated.at, "TRUE")
        self.assertEqual(validated.is_at, "FALSE")

    def test_validation_matches_minor_ocr_variants_in_mentions(self) -> None:
        document = load_jsonl(FIXTURE_PATH)[0]
        task = build_pair_tasks(document)[0]
        task = replace(
            task,
            pair=replace(
                task.pair,
                pers_mentions_list=["Delcass."],
                loc_mentions_list=["Vatikan"],
            ),
        )
        parsed = parse_model_response(
            '{"person":"Deleass.","place":"Vatikan","at_explanation":"Minor OCR variant matched.","at":"PROBABLE","isAt_explanation":"Minor OCR variant matched.","isAt":"FALSE"}'
        )
        validated = validate_prediction(task, parsed)
        self.assertEqual(validated.at, "PROBABLE")
        self.assertEqual(validated.is_at, "FALSE")


if __name__ == "__main__":
    unittest.main()
