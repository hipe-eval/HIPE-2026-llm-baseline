from __future__ import annotations

import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from hipe2026_mistral_baseline.compare_predictions import build_merged_analysis
from hipe2026_mistral_baseline.io_hipe import load_jsonl, write_jsonl


FIXTURE_PATH = Path(__file__).resolve().parent / "fixtures" / "sample_input.jsonl"


class TestComparePredictions(unittest.TestCase):
    def test_build_merged_analysis(self) -> None:
        gold_documents = load_jsonl(FIXTURE_PATH)
        gold_documents[0] = gold_documents[0].__class__(
            document_id=gold_documents[0].document_id,
            media=gold_documents[0].media,
            source=gold_documents[0].source,
            date=gold_documents[0].date,
            language=gold_documents[0].language,
            text=gold_documents[0].text,
            sampled_pairs=[
                gold_documents[0].sampled_pairs[0].with_prediction(
                    at="TRUE",
                    is_at="FALSE",
                    at_explanation="Gold at explanation",
                    is_at_explanation="Gold isAt explanation",
                )
            ],
        )

        prediction_documents = [
            gold_documents[0].__class__(
                document_id=gold_documents[0].document_id,
                media=gold_documents[0].media,
                source=gold_documents[0].source,
                date=gold_documents[0].date,
                language=gold_documents[0].language,
                text=gold_documents[0].text,
                sampled_pairs=[
                    gold_documents[0].sampled_pairs[0].with_prediction(
                        at="PROBABLE",
                        is_at="FALSE",
                        at_explanation="System at explanation",
                        is_at_explanation="System isAt explanation",
                    )
                ],
            )
        ]

        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)
            gold_path = root / "gold.jsonl"
            pred_path = root / "pred.jsonl"
            write_jsonl(gold_documents, gold_path)
            write_jsonl(prediction_documents, pred_path)

            merged = build_merged_analysis(gold_path, pred_path)

        self.assertEqual(len(merged), 3)

        first_pair = merged[0]["sampled_pairs"][0]
        self.assertEqual(
            list(first_pair.keys()),
            [
                "pers_entity_id",
                "pers_wikidata_QID",
                "pers_mentions_list",
                "loc_entity_id",
                "loc_wikidata_QID",
                "loc_mentions_list",
                "at",
                "SYS_at",
                "CORRECT_at",
                "SYS_at_explanation",
                "isAt",
                "SYS_isAt",
                "CORRECT_isAt",
                "SYS_isAt_explanation",
                "CORRECT",
            ],
        )
        self.assertEqual(first_pair["at"], "TRUE")
        self.assertEqual(first_pair["SYS_at"], "PROBABLE")
        self.assertEqual(first_pair["SYS_isAt"], "FALSE")
        self.assertEqual(first_pair["SYS_at_explanation"], "System at explanation")
        self.assertNotIn("at_explanation", first_pair)
        self.assertNotIn("isAt_explanation", first_pair)
        self.assertFalse(first_pair["CORRECT_at"])
        self.assertTrue(first_pair["CORRECT_isAt"])
        self.assertFalse(first_pair["CORRECT"])

        missing_pair = merged[1]["sampled_pairs"][0]
        self.assertEqual(missing_pair["SYS_at"], "FALSE")
        self.assertEqual(missing_pair["SYS_isAt"], "FALSE")


if __name__ == "__main__":
    unittest.main()
