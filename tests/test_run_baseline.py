from __future__ import annotations

import sys
import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from hipe2026_mistral_baseline.inference import GenerationConfig
from hipe2026_mistral_baseline.run_baseline import (
    _format_token_summary,
    _log_context_usage_summary,
    _nearest_rank_percentile,
    _project_relative_path,
    write_run_config_json,
)


class TestRunBaselineStats(unittest.TestCase):
    def test_nearest_rank_percentile(self) -> None:
        values = [10, 20, 30, 40, 50]
        self.assertEqual(_nearest_rank_percentile(values, 50), 30)
        self.assertEqual(_nearest_rank_percentile(values, 95), 50)

    def test_log_context_usage_summary(self) -> None:
        trace_records = [
            {"prompt_tokens": 100, "completion_tokens": 20, "total_tokens": 120},
            {"prompt_tokens": 200, "completion_tokens": 30, "total_tokens": 230},
            {"prompt_tokens": 300, "completion_tokens": 40, "total_tokens": 340},
        ]

        with patch("hipe2026_mistral_baseline.run_baseline.LOGGER.info") as mock_info:
            _log_context_usage_summary(trace_records, n_ctx=1024)

        self.assertEqual(mock_info.call_count, 2)
        rendered = "\n".join(call.args[1] if len(call.args) > 1 else "" for call in mock_info.call_args_list)
        self.assertIn("min=100 avg=200.0 p50=200 p95=300 max=300", rendered)
        self.assertIn("min=120 avg=230.0 p50=230 p95=340 max=340", rendered)

    def test_format_token_summary(self) -> None:
        self.assertEqual(
            _format_token_summary([100, 200, 300]),
            "min=100 avg=200.0 p50=200 p95=300 max=300",
        )

    def test_project_relative_path(self) -> None:
        absolute_path = Path.cwd() / "data/test/example.jsonl"
        self.assertEqual(
            _project_relative_path(absolute_path),
            "data/test/example.jsonl",
        )
        self.assertIsNone(_project_relative_path(None))

    def test_write_run_config_json(self) -> None:
        with tempfile.TemporaryDirectory(dir=Path.cwd()) as tmpdir:
            output_path = Path(tmpdir) / "baseline_example_run1.config.json"
            with patch("hipe2026_mistral_baseline.run_baseline.LOGGER.info"):
                write_run_config_json(
                    path=output_path,
                    input_jsonl=Path.cwd() / "data/test/example.jsonl",
                    output_jsonl=Path.cwd() / "results-test.d/baseline_example_run1.jsonl",
                    debug_jsonl=Path.cwd() / "results-test.d/debug.baseline_example_run1.jsonl",
                    prompt_file="prompts/classify_pair.txt",
                    config_file=None,
                    model_path=Path.cwd() / "hf.d/model.gguf",
                    model_source="huggingface",
                    hf_repo="repo",
                    hf_filename="model.gguf",
                    cache_dir="hf.d",
                    model_name="model-name",
                    generation_config=GenerationConfig(temperature=0.0, seed=7),
                    max_docs=3,
                )

            payload = json.loads(output_path.read_text(encoding="utf-8"))

        self.assertEqual(payload["input_jsonl"], "data/test/example.jsonl")
        self.assertEqual(
            payload["output_jsonl"],
            "results-test.d/baseline_example_run1.jsonl",
        )
        self.assertEqual(payload["model"]["hf_repo"], "repo")
        self.assertEqual(payload["generation"]["temperature"], 0.0)
        self.assertEqual(payload["generation"]["seed"], 7)
        self.assertEqual(payload["max_docs"], 3)


if __name__ == "__main__":
    unittest.main()
