"""IO helpers for the official HIPE 2026 document format."""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Iterable


AT_LABELS = {"TRUE", "PROBABLE", "FALSE"}
IS_AT_LABELS = {"TRUE", "FALSE"}


def _require_string(value: Any, field_name: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise ValueError(f"{field_name} must be a non-empty string")
    return value


def _require_nullable_string(value: Any, field_name: str) -> str | None:
    if value is None:
        return None
    if not isinstance(value, str):
        raise ValueError(f"{field_name} must be a string or null")
    return value


def _require_string_list(value: Any, field_name: str) -> list[str]:
    if not isinstance(value, list) or not value:
        raise ValueError(f"{field_name} must be a non-empty list of strings")
    items: list[str] = []
    for item in value:
        if not isinstance(item, str) or not item.strip():
            raise ValueError(f"{field_name} must contain non-empty strings")
        items.append(item)
    return items


@dataclass(frozen=True)
class Media:
    publication_title: str
    time_period: str
    source_type: str

    @classmethod
    def from_dict(cls, payload: dict[str, Any]) -> "Media":
        return cls(
            publication_title=_require_string(
                payload.get("publication_title"), "media.publication_title"
            ),
            time_period=_require_string(payload.get("time_period"), "media.time_period"),
            source_type=_require_string(payload.get("source_type"), "media.source_type"),
        )

    def to_dict(self) -> dict[str, str]:
        return {
            "publication_title": self.publication_title,
            "time_period": self.time_period,
            "source_type": self.source_type,
        }


@dataclass(frozen=True)
class SampledPair:
    pers_entity_id: str
    pers_wikidata_qid: str | None
    pers_mentions_list: list[str]
    loc_entity_id: str
    loc_wikidata_qid: str | None
    loc_mentions_list: list[str]
    at: str | None = None
    is_at: str | None = None
    at_explanation: str | None = None
    is_at_explanation: str | None = None

    @classmethod
    def from_dict(cls, payload: dict[str, Any]) -> "SampledPair":
        at = payload.get("at")
        is_at = payload.get("isAt")
        at_explanation = payload.get("at_explanation")
        is_at_explanation = payload.get("isAt_explanation")
        if at is not None:
            at = _require_string(at, "sampled_pairs[].at").upper()
            if at not in AT_LABELS:
                raise ValueError(f"Invalid at label: {at}")
        if is_at is not None:
            is_at = _require_string(is_at, "sampled_pairs[].isAt").upper()
            if is_at not in IS_AT_LABELS:
                raise ValueError(f"Invalid isAt label: {is_at}")
        return cls(
            pers_entity_id=_require_string(
                payload.get("pers_entity_id"), "sampled_pairs[].pers_entity_id"
            ),
            pers_wikidata_qid=_require_nullable_string(
                payload.get("pers_wikidata_QID"), "sampled_pairs[].pers_wikidata_QID"
            ),
            pers_mentions_list=_require_string_list(
                payload.get("pers_mentions_list"), "sampled_pairs[].pers_mentions_list"
            ),
            loc_entity_id=_require_string(
                payload.get("loc_entity_id"), "sampled_pairs[].loc_entity_id"
            ),
            loc_wikidata_qid=_require_nullable_string(
                payload.get("loc_wikidata_QID"), "sampled_pairs[].loc_wikidata_QID"
            ),
            loc_mentions_list=_require_string_list(
                payload.get("loc_mentions_list"), "sampled_pairs[].loc_mentions_list"
            ),
            at=at,
            is_at=is_at,
            at_explanation=_require_nullable_string(
                at_explanation, "sampled_pairs[].at_explanation"
            ),
            is_at_explanation=_require_nullable_string(
                is_at_explanation, "sampled_pairs[].isAt_explanation"
            ),
        )

    @property
    def person_value(self) -> str:
        return self.pers_mentions_list[0]

    @property
    def place_value(self) -> str:
        return self.loc_mentions_list[0]

    def key(self) -> tuple[str, str]:
        return (self.pers_entity_id, self.loc_entity_id)

    def with_prediction(
        self,
        *,
        at: str,
        is_at: str,
        at_explanation: str | None,
        is_at_explanation: str | None,
    ) -> "SampledPair":
        return SampledPair(
            pers_entity_id=self.pers_entity_id,
            pers_wikidata_qid=self.pers_wikidata_qid,
            pers_mentions_list=list(self.pers_mentions_list),
            loc_entity_id=self.loc_entity_id,
            loc_wikidata_qid=self.loc_wikidata_qid,
            loc_mentions_list=list(self.loc_mentions_list),
            at=at,
            is_at=is_at,
            at_explanation=at_explanation,
            is_at_explanation=is_at_explanation,
        )

    def to_dict(self) -> dict[str, Any]:
        return {
            "pers_entity_id": self.pers_entity_id,
            "pers_wikidata_QID": self.pers_wikidata_qid,
            "pers_mentions_list": list(self.pers_mentions_list),
            "loc_entity_id": self.loc_entity_id,
            "loc_wikidata_QID": self.loc_wikidata_qid,
            "loc_mentions_list": list(self.loc_mentions_list),
            "at": self.at,
            "at_explanation": self.at_explanation,
            "isAt": self.is_at,
            "isAt_explanation": self.is_at_explanation,
        }


@dataclass(frozen=True)
class HipeDocument:
    document_id: str
    media: Media
    source: str
    date: str | None
    language: str
    text: str
    sampled_pairs: list[SampledPair] = field(default_factory=list)

    @classmethod
    def from_dict(cls, payload: dict[str, Any]) -> "HipeDocument":
        sampled_pairs = payload.get("sampled_pairs")
        if not isinstance(sampled_pairs, list):
            raise ValueError("sampled_pairs must be a list")
        return cls(
            document_id=_require_string(payload.get("document_id"), "document_id"),
            media=Media.from_dict(payload.get("media") or {}),
            source=_require_string(payload.get("source"), "source"),
            date=_require_nullable_string(payload.get("date"), "date"),
            language=_require_string(payload.get("language"), "language"),
            text=_require_string(payload.get("text"), "text"),
            sampled_pairs=[SampledPair.from_dict(item) for item in sampled_pairs],
        )

    def to_dict(self) -> dict[str, Any]:
        return {
            "document_id": self.document_id,
            "media": self.media.to_dict(),
            "source": self.source,
            "date": self.date,
            "language": self.language,
            "text": self.text,
            "sampled_pairs": [pair.to_dict() for pair in self.sampled_pairs],
        }


def iter_documents(path: str | Path) -> Iterable[HipeDocument]:
    with Path(path).open("r", encoding="utf-8") as handle:
        for line_number, line in enumerate(handle, start=1):
            stripped = line.strip()
            if not stripped:
                continue
            try:
                payload = json.loads(stripped)
            except json.JSONDecodeError as exc:
                raise ValueError(f"Invalid JSON on line {line_number}: {exc}") from exc
            yield HipeDocument.from_dict(payload)


def load_jsonl(path: str | Path) -> list[HipeDocument]:
    return list(iter_documents(path))


def write_jsonl(documents: Iterable[HipeDocument], path: str | Path) -> None:
    with Path(path).open("w", encoding="utf-8") as handle:
        for document in documents:
            handle.write(json.dumps(document.to_dict(), ensure_ascii=False))
            handle.write("\n")
