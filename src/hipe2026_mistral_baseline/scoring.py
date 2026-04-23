"""Helper wrapper around the official HIPE 2026 scorer."""

from __future__ import annotations

import argparse
import subprocess
import sys
from pathlib import Path


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
    raise SystemExit(completed.returncode)
