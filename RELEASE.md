# Release 0.2.0

Second research baseline release for the HIPE-2026 person-place relation qualification task.

## What Changed

- standardized the local workflow and help text on `make` targets instead of `remake`
- updated setup so `make install` detects `nvidia-smi` and reinstalls a CUDA build of `llama-cpp-python` when an NVIDIA GPU is available
- changed the default GPU offload policy so the baseline uses full layer offload whenever the installed `llama-cpp-python` runtime reports GPU support, not only on Apple Silicon
- clarified the repository documentation around the external `HIPE-2026-data` checkout, scorer dependency, and default `make`-based workflow
- clarified the release process and made GitHub releases explicitly optional
- added the repository license file

## Default Runtime Configuration

- recommended source model: `mistralai/Ministral-3-3B-Instruct-2512`
- default Hugging Face repo: `mistralai/Ministral-3-3B-Instruct-2512-GGUF`
- default GGUF filename: `Ministral-3-3B-Instruct-2512-Q4_K_M.gguf`
- decoder: `llama-cpp-python`
- default GPU policy: if the installed runtime supports GPU offload, the baseline uses `n_gpu_layers=-1`; otherwise it stays on CPU
- expected backends include CUDA, Metal, Vulkan, HIP, and SYCL when supported by the installed runtime
- default decoding settings include `temperature=0.0` and `flash_attn=True`
- default Hugging Face cache path: `./hf.d`
- default data checkout path: `HIPE-2026-data/`
- default output paths: `results.d/predictions.{en,de,fr}.jsonl`, `results.d/debug.{en,de,fr}.jsonl`, `results.d/predictions.{en,de,fr}.diagnostic.json`
- schema labels:
  - `at`: `TRUE`, `PROBABLE`, `FALSE`
  - `isAt`: `TRUE`, `FALSE`

## Setup And Usage

- Python 3.10 or later
- Git for cloning `HIPE-2026-data`
- Python dependencies from `pyproject.toml`: `huggingface-hub`, `llama-cpp-python`, `pydantic`
- scorer dependencies from `HIPE-2026-data/requirements.txt`
- recommended setup:

```bash
python3 -m venv venv
source venv/bin/activate
make setup
```

- `make setup` creates `.env`, sets `HF_HOME=./hf.d`, installs the package, clones or updates `HIPE-2026-data/`, and installs scorer dependencies
- on NVIDIA systems, `make install` tries to switch `llama-cpp-python` to a CUDA wheel using the default `cu124` index; override `LLAMA_CPP_CUDA_INDEX` if your CUDA toolkit requires a different wheel index
- model weights are not included; use the default Hugging Face GGUF or provide `--model-path` to a local GGUF file
- main commands after setup:

```bash
make run-baseline
make evaluate-baseline
make run-all-languages
make world
```

## Notes

- this release follows the public HIPE-2026 document schema based on `sampled_pairs`
- model files and the `HIPE-2026-data` repository are not vendored into this repository
- intended as a minimal starting point for participants to extend
- for reproducibility, report the exact GGUF repo, filename, and quantization used

# Release 0.1.0

Initial research baseline release for HIPE 2026 person-place relation qualification.

## Included

- local zero-shot prompt baseline using `llama-cpp-python` with GGUF models
- scorer-compatible reading and writing of the HIPE 2026 JSONL document format
- pairwise prediction over provided `sampled_pairs`
- one default prompt template with greedy decoding by default (`temperature=0.0`)
- strict parsing and validation with conservative fallback behavior
- `make` targets for setup, baseline runs, evaluation, and diagnostics
- tests including a smoke path with fake inference

## Default Runtime Configuration

- recommended source model: `mistralai/Ministral-3-3B-Instruct-2512`
- default Hugging Face repo: `mistralai/Ministral-3-3B-Instruct-2512-GGUF`
- default GGUF filename: `Ministral-3-3B-Instruct-2512-Q4_K_M.gguf`
- decoder: `llama-cpp-python`
- on Apple Silicon macOS, the baseline will try to use Metal offload when the installed runtime supports GPU offload
- default decoding settings include `temperature=0.0` and `flash_attn=True`
- default Hugging Face cache path: `./hf.d`
- default data checkout path: `HIPE-2026-data/`
- default output paths: `results.d/predictions.{en,de,fr}.jsonl`, `results.d/debug.{en,de,fr}.jsonl`, `results.d/predictions.{en,de,fr}.diagnostic.json`
- schema labels:
  - `at`: `TRUE`, `PROBABLE`, `FALSE`
  - `isAt`: `TRUE`, `FALSE`

## Setup Requirements

- Python 3.10 or later
- Git for cloning `HIPE-2026-data`
- Python dependencies from `pyproject.toml`: `huggingface-hub`, `llama-cpp-python`, `pydantic`
- scorer dependencies from `HIPE-2026-data/requirements.txt`
- recommended setup:

```bash
python3 -m venv venv
source venv/bin/activate
make setup
```

- `make setup` creates `.env`, sets `HF_HOME=./hf.d`, installs the package, clones or updates `HIPE-2026-data/`, and installs scorer dependencies
- model weights are not included; use the default Hugging Face GGUF or provide `--model-path` to a local GGUF file

## Usage

- default no-config run path after setup:

```bash
make run-baseline
make evaluate-baseline
make run-all-languages
make world
```

## Notes

- this release follows the public HIPE 2026 document schema based on `sampled_pairs`
- model files and the `HIPE-2026-data` repository are not vendored into this repository
- intended as a minimal starting point for participants to extend
- for reproducibility, report the exact GGUF repo, filename, and quantization used
