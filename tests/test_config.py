from __future__ import annotations

import json
import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from hipe2026_mistral_baseline.run_baseline import load_run_config


class TestConfig(unittest.TestCase):
    def test_load_run_config_none(self) -> None:
        self.assertEqual(load_run_config(None), {})

    def test_load_run_config(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)
            config_dir = root / "configs"
            config_dir.mkdir()
            config_path = config_dir / "model.json"
            config_path.write_text(
                json.dumps(
                    {
                        "model_path": "models/test.gguf",
                        "prompt_file": "prompts/classify_pair.txt",
                        "temperature": 0.0,
                    }
                ),
                encoding="utf-8",
            )

            loaded = load_run_config(str(config_path))
            self.assertTrue(str(loaded["model_path"]).endswith("/models/test.gguf"))
            self.assertTrue(
                str(loaded["prompt_file"]).endswith("/prompts/classify_pair.txt")
            )
            self.assertEqual(loaded["temperature"], 0.0)


if __name__ == "__main__":
    unittest.main()
