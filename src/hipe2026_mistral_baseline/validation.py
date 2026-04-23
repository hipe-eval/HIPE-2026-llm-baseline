"""Validate parsed model predictions against the active pair."""

from __future__ import annotations

from difflib import SequenceMatcher
import re
import unicodedata
from dataclasses import dataclass

from .io_hipe import AT_LABELS, IS_AT_LABELS, SampledPair
from .pair_generation import PairTask
from .parsing import ParsedPrediction


_WHITESPACE_RE = re.compile(r"\s+")
_NON_ALNUM_RE = re.compile(r"[\W_]+", re.UNICODE)
_MAX_EXPLANATION_WORDS = 100
_MIN_FUZZY_MATCH_LENGTH = 7
_FUZZY_MATCH_RATIO = 0.85


def _normalize_surface(value: str) -> str:
    normalized = unicodedata.normalize("NFKC", value)
    normalized = normalized.replace("\\n", " ").replace("\\r", " ").replace("\\t", " ")
    normalized = normalized.replace("\n", " ").replace("\r", " ").replace("\t", " ")
    normalized = normalized.replace("\u00ad", "")
    collapsed = _WHITESPACE_RE.sub(" ", normalized).strip()
    return collapsed.strip("\"'").casefold()


def _compact_surface(value: str) -> str:
    return _NON_ALNUM_RE.sub("", _normalize_surface(value))


def _surface_matches(predicted_surface: str, mention_surfaces: list[str]) -> bool:
    predicted_normalized = _normalize_surface(predicted_surface)
    predicted_compact = _compact_surface(predicted_surface)

    for mention_surface in mention_surfaces:
        mention_normalized = _normalize_surface(mention_surface)
        if predicted_normalized == mention_normalized:
            return True

        mention_compact = _compact_surface(mention_surface)
        if predicted_compact and predicted_compact == mention_compact:
            return True

        if (
            predicted_compact
            and mention_compact
            and min(len(predicted_compact), len(mention_compact)) >= _MIN_FUZZY_MATCH_LENGTH
        ):
            if (
                predicted_compact in mention_compact
                or mention_compact in predicted_compact
            ):
                return True

            similarity = SequenceMatcher(
                None,
                predicted_compact,
                mention_compact,
                autojunk=False,
            ).ratio()
            if similarity >= _FUZZY_MATCH_RATIO:
                return True

    return False


def _normalize_evidence(value: str | None) -> str | None:
    if not value:
        return None
    collapsed = _WHITESPACE_RE.sub(" ", value).strip()
    if not collapsed:
        return None
    words = collapsed.split(" ")
    if len(words) <= _MAX_EXPLANATION_WORDS:
        return collapsed
    truncated = " ".join(words[:_MAX_EXPLANATION_WORDS]).rstrip(" ,;:")
    return f"{truncated}..."


@dataclass(frozen=True)
class ValidatedPrediction:
    at: str
    at_explanation: str | None
    is_at: str
    is_at_explanation: str | None


def _canonicalize_relation_labels(*, at: str, is_at: str) -> tuple[str, str]:
    # Immediate presence implies general presence.
    if is_at == "TRUE":
        return ("TRUE", "TRUE")
    # If the article does not support presence at all, immediate presence is impossible.
    if at == "FALSE":
        return ("FALSE", "FALSE")
    return (at, is_at)


def validate_prediction(task: PairTask, prediction: ParsedPrediction) -> ValidatedPrediction:
    if prediction.at not in AT_LABELS:
        raise ValueError(f"Invalid at label: {prediction.at}")
    if prediction.is_at not in IS_AT_LABELS:
        raise ValueError(f"Invalid isAt label: {prediction.is_at}")

    if not _surface_matches(prediction.person, task.pair.pers_mentions_list):
        raise ValueError(
            "Predicted person does not match the active pair mentions: "
            f"{prediction.person!r} vs {task.pair.pers_mentions_list!r}"
        )
    if not _surface_matches(prediction.place, task.pair.loc_mentions_list):
        raise ValueError(
            "Predicted place does not match the active pair mentions: "
            f"{prediction.place!r} vs {task.pair.loc_mentions_list!r}"
        )

    at, is_at = _canonicalize_relation_labels(
        at=prediction.at,
        is_at=prediction.is_at,
    )

    return ValidatedPrediction(
        at=at,
        at_explanation=_normalize_evidence(prediction.at_explanation),
        is_at=is_at,
        is_at_explanation=_normalize_evidence(prediction.is_at_explanation),
    )


def conservative_default_prediction(reason: str) -> ValidatedPrediction:
    message = _WHITESPACE_RE.sub(" ", reason).strip()
    return ValidatedPrediction(
        at="FALSE",
        at_explanation=_normalize_evidence(message),
        is_at="FALSE",
        is_at_explanation=_normalize_evidence(message),
    )


def apply_prediction_to_pair(pair: SampledPair, prediction: ValidatedPrediction) -> SampledPair:
    return pair.with_prediction(
        at=prediction.at,
        is_at=prediction.is_at,
        at_explanation=prediction.at_explanation,
        is_at_explanation=prediction.is_at_explanation,
    )
