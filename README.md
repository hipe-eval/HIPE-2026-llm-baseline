# HIPE-2026 Shared Task Baseline

Minimal local baseline for the [HIPE-2026 CLEF shared task](https://hipe-eval.github.io/HIPE-2026/) on **person-place relation qualification**.

This repository is intentionally small and closer to research code than framework code.
It is a zero-shot baseline: one prompt, no task-specific fine-tuning, and no few-shot examples by default.

This baseline:

- runs fully locally;
- is zero-shot by default;
- uses `llama-cpp-python` with a GGUF model;
- is built around one prompt template and deterministic greedy decoding by default;
- reads and writes the official HIPE 2026 JSONL document format;
- classifies the provided `sampled_pairs` in each document.

If you want to change the baseline, you need to touch only a few files:

- `prompts/classify_pair.txt`: change the task instructions;
- `src/hipe2026_mistral_baseline/run_baseline.py`: change the prediction loop or fallback policy;
- `src/hipe2026_mistral_baseline/inference.py`: change decoding settings or swap the local runner;
- `src/hipe2026_mistral_baseline/export.py`: change output writing.

## Schema and data format

This baseline works with the [HIPE-2026 schema](https://github.com/hipe-eval/HIPE-2026-data/blob/main/schemas/hipe-2026-data.schema.json), which organizes data as documents containing pre-sampled person-place pairs. Rather than generating predictions over a full Cartesian product of entities, the baseline classifies the pairs that are already provided in each document.

The schema defines these allowed values for the relation fields:

- `at`: `TRUE`, `PROBABLE`, `FALSE`
- `isAt`: `TRUE`, `FALSE`

The baseline preserves the input document structure and produces predictions by filling in these relation labels for each sampled pair. The official scorer expects predictions in this same document JSONL format with the relation labels populated for each pair.

## Model and runtime

Recommended source model:

- `mistralai/Ministral-3-3B-Instruct-2512`

Decoder:

- `llama-cpp-python`

The CLI expects a local GGUF file via `--model-path`. If you have a converted or mirrored GGUF on Hugging Face, you can also resolve it with `--hf-repo` and `--hf-filename`.
On Apple Silicon macOS, the baseline will try to use Metal offload automatically when the installed `llama-cpp-python` runtime supports GPU offload.
By default, the baseline also enables `flash_attn=True`.

For reproducibility, always report the exact GGUF source you used:

- Hugging Face repo id
- GGUF filename
- quantization variant

Do not assume that two GGUF files from different repos are interchangeable just because
they derive from the same original model.

## Baseline Type

This is a zero-shot prompting baseline:

- one instruction prompt template
- no few-shot examples by default
- no supervised training or task-specific fine-tuning
- no retrieval stage by default
- greedy decoding by default (`temperature=0.0` in `llama-cpp-python`)

This baseline is constrained to core functionality and preserves the option space to experiment with extensions like few-shot prompting, retrieval augmentation, or task-specific fine-tuning.

## Repository structure

```text
.
├── Makefile
├── configs/
│   └── model.example.json
├── HIPE-2026-data/
├── models/
├── results-train.d/
├── results-test.d/
├── scripts/
│   ├── evaluate_predictions.py
│   ├── compare_predictions.py
│   └── run_baseline.py
├── prompts/
│   └── classify_pair.txt
├── src/
│   └── hipe2026_mistral_baseline/
├── tests/
│   └── fixtures/
└── pyproject.toml
```

## External repositories

This baseline depends on the [HIPE-2026-data](https://github.com/hipe-eval/HIPE-2026-data) repository for:

- **data**: the official HIPE 2026 JSONL files under `data/`
- **scorer**: `scripts/file_scorer_evaluation.py` — the official evaluation script (currently bundled in the data repository; expected to move to a dedicated repository in the future)

`make setup` clones this repository automatically under `HIPE-2026-data/`.

## Local setup

Use a local `venv/` environment:

```bash
python3 -m venv venv
source venv/bin/activate
make setup
```

This:

- creates `.env`
- sets `HF_HOME=./hf.d`
- installs the package
- downloads the public HIPE 2026 data repo
- installs the official HIPE scorer dependencies from `HIPE-2026-data/requirements.txt`

The default `make run-baseline` path downloads the model from Hugging Face and
uses the project-local cache from `.env`.

If you only want to download the data later:

```bash
make install-data
```

If you only want to install the HIPE scorer dependencies later:

```bash
make install-data-deps
```

Project conventions:

- use the cloned `HIPE-2026-data/` repo directly
- let Hugging Face cache GGUF files under project-local `./hf.d/` by default
- write train predictions, debug traces, and diagnostics under `results-train.d/`
- write test predictions and debug traces under `results-test.d/`
- keep optional model defaults in `configs/`

Design choices:

- keep the main path explicit rather than abstract
- make one document loop and one pair loop easy to read
- keep parsing and validation strict, then fail back to a conservative default
- prefer small files with obvious responsibilities over a bigger framework

## Usage

Run the baseline on a HIPE JSONL file:

```bash
make run-baseline
```

This no-config path is the default intended workflow.

By default this uses:

- `HF_HOME=./hf.d`
- `mistralai/Ministral-3-3B-Instruct-2512-GGUF`
- `Ministral-3-3B-Instruct-2512-Q4_K_M.gguf`
- `flash_attn=True`

Progress logs are timestamped and updated inline for each sampled pair.

To run the baseline on the main English, German, and French files in sequence:

```bash
make run-all-languages
```

To run the full train workflow in one command:

```bash
make world
```

This runs:

- the baselines for English, German, and French
- the official evaluation on those outputs
- the merged diagnostic JSON export

The release includes the current test files under `data/test/`. Run the baseline
on the test split with:

```bash
make world-test TEST_INPUT_DIR=data/test
```

`world-test` runs only the baselines and writes test predictions and debug traces under
`results-test.d/`. It does not try to evaluate or diagnose the test split by default.
The output filename keeps the input file stem, so multiple French test files do
not overwrite one another.

By default, `world-test` expects files named:

```text
HIPE-2026-data/data/newspapers/v1.0/HIPE-2026-v1.0-impresso-test-en.jsonl
HIPE-2026-data/data/newspapers/v1.0/HIPE-2026-v1.0-impresso-test-de.jsonl
HIPE-2026-data/data/newspapers/v1.0/HIPE-2026-v1.0-impresso-test-fr.jsonl
```

For internal test files with a different basename, override only the prefix:

```bash
make world-test TEST_INPUT_PREFIX=HIPE-2026-v1.0-impresso-test-internal
```

This would read:

```text
HIPE-2026-data/data/newspapers/v1.0/HIPE-2026-v1.0-impresso-test-internal-en.jsonl
HIPE-2026-data/data/newspapers/v1.0/HIPE-2026-v1.0-impresso-test-internal-de.jsonl
HIPE-2026-data/data/newspapers/v1.0/HIPE-2026-v1.0-impresso-test-internal-fr.jsonl
```

For test files stored in another directory with the standard basenames, override
only the directory:

```bash
make world-test TEST_INPUT_DIR=data/test
```

This matches files like:

```text
data/test/HIPE-2026-v1.0-impresso-test-en.jsonl
data/test/HIPE-2026-v1.0-impresso-test-de.jsonl
data/test/HIPE-2026-v1.0-impresso-test-fr.jsonl
```

and writes:

```text
results-test.d/baseline_HIPE-2026-v1.0-impresso-test-en_run1.jsonl
results-test.d/baseline_HIPE-2026-v1.0-impresso-test-de_run1.jsonl
results-test.d/baseline_HIPE-2026-v1.0-impresso-test-fr_run1.jsonl
```

If `data/test/HIPE-2026-v1.0-surprise-test-fr.jsonl` exists, `world-test`
also writes:

```text
results-test.d/baseline_HIPE-2026-v1.0-surprise-test-fr_run1.jsonl
```

Each prediction file also gets a neighboring run configuration JSON, for example:

```text
results-test.d/baseline_HIPE-2026-v1.0-impresso-test-en_run1.config.json
```

The config file records the input/output paths, model source, resolved model path,
and generation settings such as temperature, seed, context window, and flash
attention.

The prediction files are Make targets. If an output file already exists, `make`
will not rebuild it. Use `make clean` or delete the specific output file to force
another run.

You can still override the defaults:

```bash
make run-baseline \
  INPUT_JSONL=HIPE-2026-data/data/newspapers/v1.0/HIPE-2026-v1.0-impresso-train-de.jsonl \
  OUTPUT_JSONL=results-train.d/baseline_HIPE-2026-v1.0-impresso-train-de_run1.jsonl \
  DEBUG_JSONL=results-train.d/debug.baseline_HIPE-2026-v1.0-impresso-train-de_run1.jsonl \
  RUN_CONFIG_JSON=results-train.d/baseline_HIPE-2026-v1.0-impresso-train-de_run1.config.json
```

Or use a local GGUF explicitly:

```bash
make run-baseline RUN_BASELINE_ARGS='--model-path models/your-model.gguf'
```

If you want a small amount of reusable configuration, you can optionally pass a
JSON config file for model, prompt, and decoding defaults:

```bash
python scripts/run_baseline.py \
  --config configs/model.example.json \
  --input-jsonl HIPE-2026-data/data/newspapers/v1.0/HIPE-2026-v1.0-impresso-train-en.jsonl \
  --output-jsonl results-train.d/baseline_HIPE-2026-v1.0-impresso-train-en_run1.jsonl \
  --run-config-json results-train.d/baseline_HIPE-2026-v1.0-impresso-train-en_run1.config.json
```

CLI flags override config values, so the simplest pattern is:

- keep your usual model setup in `configs/model.example.json`
- override only the input and output files on each run

Direct CLI usage with Hugging Face also works:

```bash
HF_HOME=./hf.d \
python scripts/run_baseline.py \
  --input-jsonl HIPE-2026-data/data/newspapers/v1.0/HIPE-2026-v1.0-impresso-train-en.jsonl \
  --output-jsonl results-train.d/baseline_HIPE-2026-v1.0-impresso-train-en_run1.jsonl \
  --debug-jsonl results-train.d/debug.baseline_HIPE-2026-v1.0-impresso-train-en_run1.jsonl \
  --run-config-json results-train.d/baseline_HIPE-2026-v1.0-impresso-train-en_run1.config.json \
  --hf-repo mistralai/Ministral-3-3B-Instruct-2512-GGUF \
  --hf-filename Ministral-3-3B-Instruct-2512-Q4_K_M.gguf
```

## Evaluation

If you have a local checkout of the official HIPE 2026 data repo, use the helper wrapper:

```bash
make evaluate-baseline
```

The evaluation wrapper prints both the official HIPE metrics and a per-label confusion
matrix for `at` and `isAt`.

To evaluate the main English, German, and French outputs in sequence:

```bash
make evaluate-all-languages
```

To build a merged diagnostic JSON with gold labels, system labels, explanations, and
correctness flags:

```bash
make diagnose-baseline
```

To build the same diagnostic files for English, German, and French in sequence:

```bash
make diagnose-all-languages
```

The diagnostic JSON keeps the document structure and adds, for each sampled pair:

- the gold `at` and `isAt` labels
- the system `SYS_at` and `SYS_isAt` labels
- `CORRECT_at`, `CORRECT_isAt`, and overall `CORRECT`
- separate system explanations for `at` and `isAt`

By default this evaluates:

- `OUTPUT_JSONL=results-train.d/baseline_HIPE-2026-v1.0-impresso-train-en_run1.jsonl`
- `GOLD_JSONL=$(INPUT_JSONL)`
- `SCORER_SCRIPT=HIPE-2026-data/scripts/file_scorer_evaluation.py`
- `SCHEMA_FILE=HIPE-2026-data/schemas/hipe-2026-data.schema.json`

You can override them inline, for example:

```bash
make evaluate-baseline \
  OUTPUT_JSONL=results-train.d/baseline_HIPE-2026-v1.0-impresso-train-de_run1.jsonl \
  GOLD_JSONL=HIPE-2026-data/data/newspapers/v1.0/HIPE-2026-v1.0-impresso-train-de.jsonl
```

## Testing

Run the unit tests with:

```bash
make test
```

The tests use a fake inference backend and do not require `llama-cpp-python` or model files.

## Where to start editing

Common modifications:

1. Change the prompt in `prompts/classify_pair.txt`.
2. Change the decoding defaults in `configs/model.example.json` or `src/hipe2026_mistral_baseline/inference.py`.
   On Apple Silicon, GPU offload is automatic by default unless you explicitly set `--n-gpu-layers`.
3. Change the single-pair behavior in `predict_pair()` inside `src/hipe2026_mistral_baseline/run_baseline.py`.
4. Change the fallback labels in `conservative_default_prediction()` inside `src/hipe2026_mistral_baseline/validation.py`.

If you want to add few-shot examples, the simplest path is to edit the prompt template directly.

The current baseline also tolerates some OCR noise in entity-mention matching, including
escaped line breaks and small OCR-style surface variants.
