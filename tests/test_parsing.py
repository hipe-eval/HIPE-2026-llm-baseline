from __future__ import annotations

import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from hipe2026_mistral_baseline.parsing import ParseError, parse_model_response


class TestParsing(unittest.TestCase):
    def test_parse_fenced_json(self) -> None:
        raw = """```json
        {
          "person": "Victor Hugo",
          "place": "Paris",
          "at": "TRUE",
          "isAt": "FALSE",
          "evidence": "The article says he stayed in Paris."
        }
        ```"""
        parsed = parse_model_response(raw)
        self.assertEqual(parsed.person, "Victor Hugo")
        self.assertEqual(parsed.place, "Paris")
        self.assertEqual(parsed.at, "TRUE")
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


if __name__ == "__main__":
    unittest.main()
