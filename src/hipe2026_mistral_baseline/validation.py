"""Validate parsed model predictions against the active pair."""

from __future__ import annotations

import re
from dataclasses import dataclass

from .io_hipe import AT_LABELS, IS_AT_LABELS, SampledPair
from .pair_generation import PairTask
from .parsing import ParsedPrediction


_WHITESPACE_RE = re.compile(r"\s+")


def _normalize_surface(value: str) -> str:
    collapsed = _WHITESPACE_RE.sub(" ", value).strip()
    return collapsed.strip("\"'").casefold()


@dataclass(frozen=True)
class ValidatedPrediction:
    at: str
    is_at: str
    evidence: str | None


def validate_prediction(task: PairTask, prediction: ParsedPrediction) -> ValidatedPrediction:
    if prediction.at not in AT_LABELS:
        raise ValueError(f"Invalid at label: {prediction.at}")
    if prediction.is_at not in IS_AT_LABELS:
        raise ValueError(f"Invalid isAt label: {prediction.is_at}")

    person_mentions = {_normalize_surface(item) for item in task.pair.pers_mentions_list}
    place_mentions = {_normalize_surface(item) for item in task.pair.loc_mentions_list}
    if _normalize_surface(prediction.person) not in person_mentions:
        raise ValueError(
            "Predicted person does not match the active pair mentions: "
            f"{prediction.person!r} vs {task.pair.pers_mentions_list!r}"
        )
    if _normalize_surface(prediction.place) not in place_mentions:
        raise ValueError(
            "Predicted place does not match the active pair mentions: "
            f"{prediction.place!r} vs {task.pair.loc_mentions_list!r}"
        )

    return ValidatedPrediction(
        at=prediction.at,
        is_at=prediction.is_at,
        evidence=prediction.evidence,
    )


def conservative_default_prediction(reason: str) -> ValidatedPrediction:
    message = _WHITESPACE_RE.sub(" ", reason).strip()
    return ValidatedPrediction(
        at="FALSE",
        is_at="FALSE",
        evidence=message[:240] if message else None,
    )


def apply_prediction_to_pair(pair: SampledPair, prediction: ValidatedPrediction) -> SampledPair:
    return pair.with_prediction(
        at=prediction.at,
        is_at=prediction.is_at,
        at_explanation=prediction.evidence,
        is_at_explanation=prediction.evidence,
    )
