"""Merge gold and system HIPE JSONL files into one JSON analysis file."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from .io_hipe import HipeDocument, SampledPair, load_jsonl


def build_arg_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Merge gold and system prediction JSONL files into one JSON file."
    )
    parser.add_argument("--gold-jsonl", required=True, help="Gold HIPE JSONL file.")
    parser.add_argument(
        "--predictions-jsonl",
        required=True,
        help="System predictions JSONL file.",
    )
    parser.add_argument(
        "--output-json",
        required=True,
        help="Merged analysis JSON file to write.",
    )
    return parser


def _documents_by_id(path: str | Path) -> dict[str, HipeDocument]:
    return {document.document_id: document for document in load_jsonl(path)}


def _pairs_by_key(document: HipeDocument) -> dict[tuple[str, str], SampledPair]:
    return {pair.key(): pair for pair in document.sampled_pairs}


def _prediction_fields(pair: SampledPair | None) -> tuple[str, str, str | None, str | None]:
    if pair is None:
        return ("FALSE", "FALSE", None, None)
    return (
        pair.at or "FALSE",
        pair.is_at or "FALSE",
        pair.at_explanation,
        pair.is_at_explanation,
    )


def build_merged_analysis(
    gold_jsonl: str | Path,
    predictions_jsonl: str | Path,
) -> list[dict[str, object]]:
    gold_documents = _documents_by_id(gold_jsonl)
    prediction_documents = _documents_by_id(predictions_jsonl)
    merged_documents: list[dict[str, object]] = []

    for document_id, gold_document in gold_documents.items():
        prediction_document = prediction_documents.get(document_id)
        prediction_pairs = (
            _pairs_by_key(prediction_document) if prediction_document is not None else {}
        )

        merged_pairs: list[dict[str, object]] = []
        for gold_pair in gold_document.sampled_pairs:
            system_pair = prediction_pairs.get(gold_pair.key())
            sys_at, sys_is_at, sys_at_explanation, sys_is_at_explanation = _prediction_fields(
                system_pair
            )

            merged_pairs.append(
                {
                    "pers_entity_id": gold_pair.pers_entity_id,
                    "pers_wikidata_QID": gold_pair.pers_wikidata_qid,
                    "pers_mentions_list": list(gold_pair.pers_mentions_list),
                    "loc_entity_id": gold_pair.loc_entity_id,
                    "loc_wikidata_QID": gold_pair.loc_wikidata_qid,
                    "loc_mentions_list": list(gold_pair.loc_mentions_list),
                    "at": gold_pair.at,
                    "SYS_at": sys_at,
                    "CORRECT_at": sys_at == gold_pair.at,
                    "SYS_at_explanation": sys_at_explanation,
                    "isAt": gold_pair.is_at,
                    "SYS_isAt": sys_is_at,
                    "CORRECT_isAt": sys_is_at == gold_pair.is_at,
                    "SYS_isAt_explanation": sys_is_at_explanation,
                    "CORRECT": (sys_at == gold_pair.at) and (sys_is_at == gold_pair.is_at),
                }
            )

        merged_documents.append(
            {
                "document_id": gold_document.document_id,
                "media": gold_document.media.to_dict(),
                "source": gold_document.source,
                "date": gold_document.date,
                "language": gold_document.language,
                "text": gold_document.text,
                "sampled_pairs": merged_pairs,
            }
        )

    return merged_documents


def write_merged_analysis(documents: list[dict[str, object]], path: str | Path) -> None:
    output_path = Path(path).expanduser().resolve()
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with output_path.open("w", encoding="utf-8") as handle:
        json.dump(documents, handle, ensure_ascii=False, indent=2)
        handle.write("\n")


def main() -> None:
    args = build_arg_parser().parse_args()
    merged = build_merged_analysis(args.gold_jsonl, args.predictions_jsonl)
    write_merged_analysis(merged, args.output_json)


if __name__ == "__main__":
    main()
