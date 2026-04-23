from __future__ import annotations

import json
import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from hipe2026_mistral_baseline.io_hipe import load_jsonl, write_jsonl
from hipe2026_mistral_baseline.scoring import (
    build_confusion_matrix,
    collect_gold_and_predicted_labels,
    format_confusion_matrix,
)


FIXTURE_PATH = Path(__file__).resolve().parent / "fixtures" / "sample_input.jsonl"


class TestScoring(unittest.TestCase):
    def test_collect_labels_and_confusion_matrix(self) -> None:
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
                    at_explanation=None,
                    is_at_explanation=None,
                )
            ],
        )
        gold_documents[1] = gold_documents[1].__class__(
            document_id=gold_documents[1].document_id,
            media=gold_documents[1].media,
            source=gold_documents[1].source,
            date=gold_documents[1].date,
            language=gold_documents[1].language,
            text=gold_documents[1].text,
            sampled_pairs=[
                gold_documents[1].sampled_pairs[0].with_prediction(
                    at="PROBABLE",
                    is_at="TRUE",
                    at_explanation=None,
                    is_at_explanation=None,
                )
            ],
        )
        gold_documents[2] = gold_documents[2].__class__(
            document_id=gold_documents[2].document_id,
            media=gold_documents[2].media,
            source=gold_documents[2].source,
            date=gold_documents[2].date,
            language=gold_documents[2].language,
            text=gold_documents[2].text,
            sampled_pairs=[
                gold_documents[2].sampled_pairs[0].with_prediction(
                    at="FALSE",
                    is_at="FALSE",
                    at_explanation=None,
                    is_at_explanation=None,
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
                        at_explanation=None,
                        is_at_explanation=None,
                    )
                ],
            ),
            gold_documents[1].__class__(
                document_id=gold_documents[1].document_id,
                media=gold_documents[1].media,
                source=gold_documents[1].source,
                date=gold_documents[1].date,
                language=gold_documents[1].language,
                text=gold_documents[1].text,
                sampled_pairs=[
                    gold_documents[1].sampled_pairs[0].with_prediction(
                        at="PROBABLE",
                        is_at="FALSE",
                        at_explanation=None,
                        is_at_explanation=None,
                    )
                ],
            ),
        ]

        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)
            gold_path = root / "gold.jsonl"
            pred_path = root / "pred.jsonl"
            write_jsonl(gold_documents, gold_path)
            write_jsonl(prediction_documents, pred_path)

            labels = collect_gold_and_predicted_labels(gold_path, pred_path)

        self.assertEqual(labels["at"]["gold"], ["TRUE", "PROBABLE", "FALSE"])
        self.assertEqual(labels["at"]["pred"], ["PROBABLE", "PROBABLE", "FALSE"])
        self.assertEqual(labels["isAt"]["gold"], ["FALSE", "TRUE", "FALSE"])
        self.assertEqual(labels["isAt"]["pred"], ["FALSE", "FALSE", "FALSE"])

        at_matrix = build_confusion_matrix(
            labels["at"]["gold"],
            labels["at"]["pred"],
            ["TRUE", "PROBABLE", "FALSE"],
        )
        self.assertEqual(at_matrix, [[0, 1, 0], [0, 1, 0], [0, 0, 1]])

        rendered = format_confusion_matrix(
            title="at",
            label_order=["TRUE", "PROBABLE", "FALSE"],
            matrix=at_matrix,
        )
        self.assertIn("gold\\pred", rendered)
        self.assertIn("PROBABLE", rendered)
        self.assertIn("support", rendered)


if __name__ == "__main__":
    unittest.main()
