"""Prompt loading and rendering."""

from __future__ import annotations

from pathlib import Path

from .pair_generation import PairTask


DEFAULT_PROMPT_PATH = Path(__file__).resolve().parents[2] / "prompts" / "classify_pair.txt"


def load_prompt_template(path: str | Path | None = None) -> str:
    prompt_path = Path(path) if path else DEFAULT_PROMPT_PATH
    return prompt_path.read_text(encoding="utf-8")


def _format_mentions(values: list[str]) -> str:
    return " | ".join(values)


def _build_pair_context(task: PairTask) -> str:
    pair = task.pair
    return (
        "Pair to classify:\n"
        f"Person entity id: {pair.pers_entity_id}\n"
        f"Person wikidata QID: {pair.pers_wikidata_qid or 'null'}\n"
        f"Person mentions: {_format_mentions(pair.pers_mentions_list)}\n\n"
        f"Place entity id: {pair.loc_entity_id}\n"
        f"Place wikidata QID: {pair.loc_wikidata_qid or 'null'}\n"
        f"Place mentions: {_format_mentions(pair.loc_mentions_list)}\n\n"
        "Return exactly this JSON shape, in this field order:\n"
        "{\n"
        f'  "person": "{pair.person_value}",\n'
        f'  "place": "{pair.place_value}",\n'
        '  "at_explanation": "concise text-grounded explanation, max 100 words",\n'
        '  "at": "TRUE|PROBABLE|FALSE",\n'
        '  "isAt_explanation": "concise text-grounded explanation, max 100 words",\n'
        '  "isAt": "TRUE|FALSE"\n'
        "}\n"
    )


def build_prompt(task: PairTask, template: str) -> str:
    pair = task.pair
    return template.format(
        language=task.language,
        publication_date=task.publication_date or "unknown",
        person_id=pair.pers_entity_id,
        person_qid=pair.pers_wikidata_qid or "null",
        person_mentions=_format_mentions(pair.pers_mentions_list),
        person_value=pair.person_value,
        place_id=pair.loc_entity_id,
        place_qid=pair.loc_wikidata_qid or "null",
        place_mentions=_format_mentions(pair.loc_mentions_list),
        place_value=pair.place_value,
        article_text=task.text,
        pair_context=_build_pair_context(task),
    )
