from __future__ import annotations

import sys
import unittest
from pathlib import Path
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from hipe2026_mistral_baseline.run_baseline import (
    _format_token_summary,
    _log_context_usage_summary,
    _nearest_rank_percentile,
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


if __name__ == "__main__":
    unittest.main()
