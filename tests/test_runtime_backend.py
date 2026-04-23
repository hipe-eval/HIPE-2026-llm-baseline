from __future__ import annotations

import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from hipe2026_mistral_baseline.inference import describe_runtime_backend


class TestRuntimeBackend(unittest.TestCase):
    def test_describe_runtime_backend_metal(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            lib_dir = Path(tmpdir)
            (lib_dir / "libggml-metal.dylib").write_text("", encoding="utf-8")
            backend = describe_runtime_backend(
                supports_gpu_offload=True,
                n_gpu_layers=-1,
                lib_dir=lib_dir,
            )
            self.assertEqual(backend, "metal")

    def test_describe_runtime_backend_cpu(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            backend = describe_runtime_backend(
                supports_gpu_offload=False,
                n_gpu_layers=0,
                lib_dir=Path(tmpdir),
            )
            self.assertEqual(backend, "cpu")


if __name__ == "__main__":
    unittest.main()
