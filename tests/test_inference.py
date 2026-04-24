from __future__ import annotations

import sys
import unittest
from pathlib import Path
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from hipe2026_mistral_baseline.inference import auto_n_gpu_layers


class TestInferenceDefaults(unittest.TestCase):
    def test_auto_n_gpu_layers_uses_gpu_when_supported(self) -> None:
        self.assertEqual(auto_n_gpu_layers(supports_gpu_offload=True), -1)

    def test_auto_n_gpu_layers_uses_cpu_when_gpu_not_supported(self) -> None:
        self.assertEqual(auto_n_gpu_layers(supports_gpu_offload=False), 0)

    def test_auto_n_gpu_layers_uses_gpu_on_macos_arm_when_supported(self) -> None:
        with patch("platform.system", return_value="Darwin"), patch(
            "platform.machine", return_value="arm64"
        ):
            self.assertEqual(auto_n_gpu_layers(supports_gpu_offload=True), -1)

    def test_auto_n_gpu_layers_uses_cpu_on_macos_arm_when_gpu_not_supported(self) -> None:
        with patch("platform.system", return_value="Darwin"), patch(
            "platform.machine", return_value="arm64"
        ):
            self.assertEqual(auto_n_gpu_layers(supports_gpu_offload=False), 0)


if __name__ == "__main__":
    unittest.main()