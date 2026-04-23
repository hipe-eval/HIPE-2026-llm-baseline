"""CLI entrypoint for the HIPE 2026 local prompt baseline."""

from __future__ import annotations

import argparse
import json
from dataclasses import dataclass
from pathlib import Path

from .export import write_debug_jsonl, write_submission_jsonl
from .inference import DEFAULT_MODEL_NAME, GenerationConfig, LlamaCppRunner, resolve_model_path
from .io_hipe import HipeDocument, load_jsonl
from .pair_generation import build_pair_tasks
from .pair_generation import PairTask
from .parsing import ParseError, parse_model_response
from .prompting import build_prompt, load_prompt_template
from .validation import (
    apply_prediction_to_pair,
    conservative_default_prediction,
    validate_prediction,
)


@dataclass(frozen=True)
class TraceRecord:
    document_id: str
    pers_entity_id: str
    loc_entity_id: str
    prompt: str
    raw_output: str
    at: str
    is_at: str
    used_default: bool
    error: str | None

    def to_dict(self) -> dict[str, object]:
        return {
            "document_id": self.document_id,
            "pers_entity_id": self.pers_entity_id,
            "loc_entity_id": self.loc_entity_id,
            "prompt": self.prompt,
            "raw_output": self.raw_output,
            "at": self.at,
            "isAt": self.is_at,
            "used_default": self.used_default,
            "error": self.error,
        }


def predict_pair(task: PairTask, *, runner, prompt_template: str) -> tuple[object, dict[str, object]]:
    """Predict one sampled pair.

    This is the main function to edit if you want to experiment with:
    - alternate prompts
    - separate prompts for `at` and `isAt`
    - repair steps after JSON parsing failure
    - retrieval or sentence filtering before prompting
    """

    prompt = build_prompt(task, prompt_template)
    raw_output = runner.generate(prompt)
    used_default = False
    error: str | None = None
    try:
        parsed = parse_model_response(raw_output)
        validated = validate_prediction(task, parsed)
    except (ParseError, ValueError) as exc:
        used_default = True
        error = str(exc)
        validated = conservative_default_prediction(str(exc))

    updated_pair = apply_prediction_to_pair(task.pair, validated)
    trace_record = TraceRecord(
        document_id=task.document_id,
        pers_entity_id=task.pair.pers_entity_id,
        loc_entity_id=task.pair.loc_entity_id,
        prompt=prompt,
        raw_output=raw_output,
        at=validated.at,
        is_at=validated.is_at,
        used_default=used_default,
        error=error,
    ).to_dict()
    return updated_pair, trace_record


def run_documents(
    documents: list[HipeDocument],
    *,
    runner,
    prompt_template: str,
) -> tuple[list[HipeDocument], list[dict[str, object]]]:
    """Run the full baseline over a list of documents.

    The structure is intentionally plain:
    1. iterate over documents
    2. iterate over sampled pairs
    3. predict one pair
    4. rebuild the document with predicted labels
    """

    output_documents: list[HipeDocument] = []
    trace_records: list[dict[str, object]] = []

    for document in documents:
        predicted_pairs = []
        for task in build_pair_tasks(document):
            predicted_pair, trace_record = predict_pair(
                task,
                runner=runner,
                prompt_template=prompt_template,
            )
            predicted_pairs.append(predicted_pair)
            trace_records.append(trace_record)

        output_documents.append(
            HipeDocument(
                document_id=document.document_id,
                media=document.media,
                source=document.source,
                date=document.date,
                language=document.language,
                text=document.text,
                sampled_pairs=predicted_pairs,
            )
        )

    return output_documents, trace_records


def load_run_config(path: str | None) -> dict[str, object]:
    """Load a small optional JSON config for model and decoding defaults."""

    if not path:
        return {}

    config_path = Path(path).expanduser().resolve()
    with config_path.open("r", encoding="utf-8") as handle:
        payload = json.load(handle)
    if not isinstance(payload, dict):
        raise ValueError("Config file must contain a JSON object")

    resolved: dict[str, object] = {}
    for key, value in payload.items():
        if key in {"model_path", "prompt_file", "cache_dir"} and isinstance(value, str):
            resolved[key] = str((config_path.parent.parent / value).resolve())
        else:
            resolved[key] = value
    return resolved


def build_arg_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Run a local prompt baseline for HIPE 2026 sampled_pairs."
    )
    parser.add_argument(
        "--config",
        help="Optional JSON config file for model, prompt, and decoding defaults.",
    )
    parser.add_argument("--input-jsonl", required=True, help="Input HIPE JSONL file.")
    parser.add_argument("--output-jsonl", required=True, help="Prediction JSONL file.")
    parser.add_argument(
        "--debug-jsonl",
        help="Optional debug JSONL file with prompts, raw outputs, and fallbacks.",
    )
    parser.add_argument("--prompt-file", default=None, help="Override the prompt template file.")
    parser.add_argument("--model-path", default=None, help="Local GGUF model path.")
    parser.add_argument("--hf-repo", default=None, help="Hugging Face repo containing a GGUF file.")
    parser.add_argument("--hf-filename", default=None, help="GGUF filename in the Hugging Face repo.")
    parser.add_argument("--cache-dir", default=None, help="Optional Hugging Face cache directory.")
    parser.add_argument("--max-docs", type=int, help="Limit documents for quick runs.")
    parser.add_argument("--temperature", type=float, default=None)
    parser.add_argument("--seed", type=int, default=None)
    parser.add_argument("--max-tokens", type=int, default=None)
    parser.add_argument("--top-p", type=float, default=None)
    parser.add_argument("--top-k", type=int, default=None)
    parser.add_argument("--repeat-penalty", type=float, default=None)
    parser.add_argument("--n-ctx", type=int, default=None)
    parser.add_argument("--n-gpu-layers", type=int, default=None)
    parser.add_argument(
        "--model-name",
        default=None,
        help="Metadata only. Used for documentation and reproducibility logs.",
    )
    return parser


def _setting(
    args: argparse.Namespace,
    config: dict[str, object],
    name: str,
    default: object | None = None,
):
    value = getattr(args, name)
    if value is not None:
        return value
    if name in config:
        return config[name]
    return default


def main() -> None:
    parser = build_arg_parser()
    args = parser.parse_args()
    config_values = load_run_config(args.config)

    documents = load_jsonl(args.input_jsonl)
    if args.max_docs is not None:
        documents = documents[: args.max_docs]

    prompt_template = load_prompt_template(_setting(args, config_values, "prompt_file"))
    config = GenerationConfig(
        temperature=float(_setting(args, config_values, "temperature", 0.0)),
        seed=int(_setting(args, config_values, "seed", 42)),
        max_tokens=int(_setting(args, config_values, "max_tokens", 256)),
        top_p=float(_setting(args, config_values, "top_p", 0.95)),
        top_k=int(_setting(args, config_values, "top_k", 40)),
        repeat_penalty=float(_setting(args, config_values, "repeat_penalty", 1.0)),
        n_ctx=int(_setting(args, config_values, "n_ctx", 8192)),
        n_gpu_layers=int(_setting(args, config_values, "n_gpu_layers", 0)),
    )
    model_path = resolve_model_path(
        model_path=_setting(args, config_values, "model_path"),
        hf_repo=_setting(args, config_values, "hf_repo"),
        hf_filename=_setting(args, config_values, "hf_filename"),
        cache_dir=_setting(args, config_values, "cache_dir"),
    )
    runner = LlamaCppRunner(model_path=model_path, config=config)

    predicted_documents, debug_records = run_documents(
        documents,
        runner=runner,
        prompt_template=prompt_template,
    )
    write_submission_jsonl(predicted_documents, args.output_jsonl)
    if args.debug_jsonl:
        write_debug_jsonl(debug_records, args.debug_jsonl)

    print(
        f"Processed {len(predicted_documents)} documents with model "
        f"{_setting(args, config_values, 'model_name', DEFAULT_MODEL_NAME)} "
        f"from {Path(model_path).name}"
    )


if __name__ == "__main__":
    main()
