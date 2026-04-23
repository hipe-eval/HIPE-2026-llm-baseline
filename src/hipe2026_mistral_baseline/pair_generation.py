"""Build pair-level tasks from HIPE documents."""

from __future__ import annotations

from dataclasses import dataclass

from .io_hipe import HipeDocument, SampledPair


@dataclass(frozen=True)
class PairTask:
    document_id: str
    language: str
    publication_date: str | None
    text: str
    pair: SampledPair


def build_pair_tasks(document: HipeDocument) -> list[PairTask]:
    return [
        PairTask(
            document_id=document.document_id,
            language=document.language,
            publication_date=document.date,
            text=document.text,
            pair=pair,
        )
        for pair in document.sampled_pairs
    ]
