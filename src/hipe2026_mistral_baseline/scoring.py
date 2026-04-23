"""Helper wrapper around the official HIPE 2026 scorer."""

from __future__ import annotations

import argparse
import subprocess
import sys
from pathlib import Path

from .io_hipe import AT_LABELS, HipeDocument, IS_AT_LABELS, SampledPair, load_jsonl


def build_arg_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Run the official HIPE 2026 scorer on a prediction file."
    )
    parser.add_argument(
        "--scorer-script",
        required=True,
        help="Path to HIPE-2026-data/scripts/file_scorer_evaluation.py",
    )
    parser.add_argument(
        "--schema-file",
        required=True,
        help="Path to HIPE-2026-data/schemas/hipe-2026-data.schema.json",
    )
    parser.add_argument("--gold-jsonl", required=True, help="Gold JSONL file.")
    parser.add_argument(
        "--predictions-jsonl",
        required=True,
        help="Predictions JSONL file produced by this baseline.",
    )
    parser.add_argument(
        "--python",
        default=sys.executable,
        help="Python interpreter used to launch the official scorer.",
    )
    return parser


def _documents_by_id(path: str | Path) -> dict[str, HipeDocument]:
    return {document.document_id: document for document in load_jsonl(path)}


def _pairs_by_key(document: HipeDocument) -> dict[tuple[str, str], SampledPair]:
    return {pair.key(): pair for pair in document.sampled_pairs}


def _default_prediction_for_missing_pair() -> tuple[str, str]:
    return ("FALSE", "FALSE")


def collect_gold_and_predicted_labels(
    gold_jsonl: str | Path,
    predictions_jsonl: str | Path,
) -> dict[str, dict[str, list[str]]]:
    gold_documents = _documents_by_id(gold_jsonl)
    prediction_documents = _documents_by_id(predictions_jsonl)
    labels = {"at": {"gold": [], "pred": []}, "isAt": {"gold": [], "pred": []}}

    for document_id, gold_document in gold_documents.items():
        gold_pairs = _pairs_by_key(gold_document)
        prediction_document = prediction_documents.get(document_id)
        prediction_pairs = (
            _pairs_by_key(prediction_document) if prediction_document is not None else {}
        )

        for key, gold_pair in gold_pairs.items():
            prediction_pair = prediction_pairs.get(key)
            if prediction_pair is None:
                predicted_at, predicted_is_at = _default_prediction_for_missing_pair()
            else:
                predicted_at = prediction_pair.at or "FALSE"
                predicted_is_at = prediction_pair.is_at or "FALSE"

            if gold_pair.at is None or gold_pair.is_at is None:
                raise ValueError(
                    "Gold file must contain non-null 'at' and 'isAt' labels for evaluation"
                )

            labels["at"]["gold"].append(gold_pair.at)
            labels["at"]["pred"].append(predicted_at)
            labels["isAt"]["gold"].append(gold_pair.is_at)
            labels["isAt"]["pred"].append(predicted_is_at)

    return labels


def build_confusion_matrix(
    gold: list[str],
    pred: list[str],
    label_order: list[str],
) -> list[list[int]]:
    index_by_label = {label: index for index, label in enumerate(label_order)}
    matrix = [[0 for _ in label_order] for _ in label_order]

    for gold_label, pred_label in zip(gold, pred):
        matrix[index_by_label[gold_label]][index_by_label[pred_label]] += 1

    return matrix


def format_confusion_matrix(
    *,
    title: str,
    label_order: list[str],
    matrix: list[list[int]],
) -> str:
    row_header = "gold\\pred"
    support_header = "support"
    first_col_width = max(len(row_header), *(len(label) for label in label_order))
    cell_width = max(
        5,
        *(len(label) for label in label_order),
        *(len(str(value)) for row in matrix for value in row),
    )
    support_width = max(
        len(support_header),
        *(len(str(sum(row))) for row in matrix),
    )

    lines = [f"{title}:"]
    header = row_header.ljust(first_col_width) + "  " + "  ".join(
        label.rjust(cell_width) for label in label_order
    ) + "  " + support_header.rjust(support_width)
    lines.append(header)

    for row_label, row in zip(label_order, matrix):
        lines.append(
            row_label.ljust(first_col_width)
            + "  "
            + "  ".join(str(value).rjust(cell_width) for value in row)
            + "  "
            + str(sum(row)).rjust(support_width)
        )

    return "\n".join(lines)


def print_confusion_matrices(gold_jsonl: str | Path, predictions_jsonl: str | Path) -> None:
    labels = collect_gold_and_predicted_labels(gold_jsonl, predictions_jsonl)
    target_specs = [
        ("at", ["TRUE", "PROBABLE", "FALSE"]),
        ("isAt", ["TRUE", "FALSE"]),
    ]

    print("\nConfusion Matrices:")
    for target, label_order in target_specs:
        matrix = build_confusion_matrix(
            labels[target]["gold"],
            labels[target]["pred"],
            label_order,
        )
        print(
            format_confusion_matrix(
                title=target,
                label_order=label_order,
                matrix=matrix,
            )
        )
        print()


def main() -> None:
    args = build_arg_parser().parse_args()
    command = [
        args.python,
        str(Path(args.scorer_script).expanduser().resolve()),
        "--schema_file",
        str(Path(args.schema_file).expanduser().resolve()),
        "--gold_data_file",
        str(Path(args.gold_jsonl).expanduser().resolve()),
        "--predictions_file",
        str(Path(args.predictions_jsonl).expanduser().resolve()),
    ]
    completed = subprocess.run(command, check=False)
    if completed.returncode == 0:
        print_confusion_matrices(args.gold_jsonl, args.predictions_jsonl)
    raise SystemExit(completed.returncode)
