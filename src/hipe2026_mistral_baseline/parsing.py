"""Strict JSON parsing for model responses."""

from __future__ import annotations

import json
import re
from dataclasses import dataclass


class ParseError(ValueError):
    """Raised when model output cannot be parsed into the expected JSON form."""


@dataclass(frozen=True)
class ParsedPrediction:
    person: str
    place: str
    at: str
    is_at: str
    evidence: str | None


_TRAILING_COMMA_RE = re.compile(r",(\s*[}\]])")


def _strip_code_fences(raw_text: str) -> str:
    text = raw_text.strip()
    if text.startswith("```") and text.endswith("```"):
        lines = text.splitlines()
        if len(lines) >= 3:
            return "\n".join(lines[1:-1]).strip()
    return text


def _extract_json_object(raw_text: str) -> str:
    text = _strip_code_fences(raw_text)
    start = text.find("{")
    if start == -1:
        raise ParseError("No JSON object start found in model output")

    depth = 0
    in_string = False
    escaped = False
    for index in range(start, len(text)):
        char = text[index]
        if in_string:
            if escaped:
                escaped = False
            elif char == "\\":
                escaped = True
            elif char == '"':
                in_string = False
            continue

        if char == '"':
            in_string = True
        elif char == "{":
            depth += 1
        elif char == "}":
            depth -= 1
            if depth == 0:
                return text[start : index + 1]

    raise ParseError("Unbalanced JSON object in model output")


def _load_json_candidate(raw_text: str) -> dict[str, object]:
    candidate = _extract_json_object(raw_text)
    try:
        payload = json.loads(candidate)
    except json.JSONDecodeError:
        repaired = _TRAILING_COMMA_RE.sub(r"\1", candidate)
        try:
            payload = json.loads(repaired)
        except json.JSONDecodeError as exc:
            raise ParseError(f"Invalid JSON response: {exc}") from exc

    if not isinstance(payload, dict):
        raise ParseError("Model output JSON must be an object")
    return payload


def parse_model_response(raw_text: str) -> ParsedPrediction:
    payload = _load_json_candidate(raw_text)
    required_fields = ["person", "place", "at", "isAt"]
    missing = [field for field in required_fields if field not in payload]
    if missing:
        raise ParseError(f"Missing required fields: {', '.join(missing)}")

    person = payload["person"]
    place = payload["place"]
    at = payload["at"]
    is_at = payload["isAt"]
    evidence = payload.get("evidence")

    if not isinstance(person, str) or not person.strip():
        raise ParseError("person must be a non-empty string")
    if not isinstance(place, str) or not place.strip():
        raise ParseError("place must be a non-empty string")
    if not isinstance(at, str) or not at.strip():
        raise ParseError("at must be a non-empty string")
    if not isinstance(is_at, str) or not is_at.strip():
        raise ParseError("isAt must be a non-empty string")
    if evidence is not None and not isinstance(evidence, str):
        raise ParseError("evidence must be a string or null")

    return ParsedPrediction(
        person=person.strip(),
        place=place.strip(),
        at=at.strip().upper(),
        is_at=is_at.strip().upper(),
        evidence=evidence.strip() if isinstance(evidence, str) and evidence.strip() else None,
    )
