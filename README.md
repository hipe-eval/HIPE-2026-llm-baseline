# HIPE 2026 Mistral Baseline

Minimal local baseline for the HIPE 2026 CLEF task on person-place relation qualification.

This repo is intentionally small and closer to research code than framework code.
It is a zero-shot baseline: one prompt, no task-specific fine-tuning, and no few-shot examples by default.

This baseline:

- runs fully locally
- is zero-shot by default
- uses `llama-cpp-python` with a GGUF model
- is built around one prompt template and deterministic greedy decoding by default
- reads and writes the official HIPE 2026 JSONL document format
- classifies the provided `sampled_pairs` in each document

If you want to change the baseline, you should mostly need to touch only a few files:

- `prompts/classify_pair.txt`: change the task instructions
- `src/hipe2026_mistral_baseline/run_baseline.py`: change the prediction loop or fallback policy
- `src/hipe2026_mistral_baseline/inference.py`: change decoding settings or swap the local runner
- `src/hipe2026_mistral_baseline/export.py`: change output writing

## Important schema note

The released HIPE 2026 schema uses `sampled_pairs` inside each document. That means the official scorer expects predictions in the same document JSONL shape, with labels filled in for each sampled person-place pair.

The current public schema allows:

- `at`: `TRUE`, `PROBABLE`, `FALSE`
- `isAt`: `TRUE`, `FALSE`

So this baseline preserves the document structure and predicts labels per sampled pair rather than rebuilding a full Cartesian product over all entities.

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

Participants can extend it with few-shot prompting, sentence selection, retrieval, or a classifier later.

## Layout

```text
.
├── Makefile
├── configs/
│   └── model.example.json
├── HIPE-2026-data/
├── models/
├── outputs/
├── scripts/
│   ├── evaluate_predictions.py
│   └── run_baseline.py
├── prompts/
│   └── classify_pair.txt
├── src/
│   └── hipe2026_mistral_baseline/
├── tests/
│   └── fixtures/
└── pyproject.toml
```

## Local setup

Use a local `venv/` environment:

```bash
python3 -m venv venv
source venv/bin/activate
remake setup
```

This:

- creates `.env`
- sets `HF_HOME=./hf.d`
- installs the package
- downloads the public HIPE 2026 data repo
- installs the official HIPE scorer dependencies from `HIPE-2026-data/requirements.txt`

The default `remake run-baseline` path downloads the model from Hugging Face and
uses the project-local cache from `.env`.

If you only want to download the data later:

```bash
remake install-data
```

If you only want to install the HIPE scorer dependencies later:

```bash
remake install-data-deps
```

Project conventions:

- use the cloned `HIPE-2026-data/` repo directly
- let Hugging Face cache GGUF files under project-local `./hf.d/` by default
- write predictions and debug traces under `outputs/`
- keep optional model defaults in `configs/`

Design choices:

- keep the main path explicit rather than abstract
- make one document loop and one pair loop easy to read
- keep parsing and validation strict, then fail back to a conservative default
- prefer small files with obvious responsibilities over a bigger framework

## Usage

Run the baseline on a HIPE JSONL file:

```bash
remake run-baseline
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
remake run-all-languages
```

The prediction files are Make targets. If an output file already exists, `remake`
will not rebuild it. Use `remake clean` or delete the specific output file to force
another run.

You can still override the defaults:

```bash
remake run-baseline \
  INPUT_JSONL=HIPE-2026-data/data/newspapers/v1.0/HIPE-2026-v1.0-impresso-train-de.jsonl \
  OUTPUT_JSONL=outputs/predictions.de.jsonl \
  DEBUG_JSONL=outputs/debug.de.jsonl
```

Or use a local GGUF explicitly:

```bash
remake run-baseline RUN_BASELINE_ARGS='--model-path models/your-model.gguf'
```

If you want a small amount of reusable configuration, you can optionally pass a
JSON config file for model, prompt, and decoding defaults:

```bash
python scripts/run_baseline.py \
  --config configs/model.example.json \
  --input-jsonl HIPE-2026-data/data/newspapers/v1.0/HIPE-2026-v1.0-impresso-train-en.jsonl \
  --output-jsonl outputs/predictions.en.jsonl
```

CLI flags override config values, so the simplest pattern is:

- keep your usual model setup in `configs/model.example.json`
- override only the input and output files on each run

Direct CLI usage with Hugging Face also works:

```bash
HF_HOME=./hf.d \
python scripts/run_baseline.py \
  --input-jsonl HIPE-2026-data/data/newspapers/v1.0/HIPE-2026-v1.0-impresso-train-en.jsonl \
  --output-jsonl outputs/predictions.en.jsonl \
  --debug-jsonl outputs/debug.en.jsonl \
  --hf-repo mistralai/Ministral-3-3B-Instruct-2512-GGUF \
  --hf-filename Ministral-3-3B-Instruct-2512-Q4_K_M.gguf
```

## Evaluation

If you have a local checkout of the official HIPE 2026 data repo, use the helper wrapper:

```bash
remake evaluate-baseline
```

To evaluate the main English, German, and French outputs in sequence:

```bash
remake evaluate-all-languages
```

By default this evaluates:

- `OUTPUT_JSONL=outputs/predictions.en.jsonl`
- `GOLD_JSONL=$(INPUT_JSONL)`
- `SCORER_SCRIPT=HIPE-2026-data/scripts/file_scorer_evaluation.py`
- `SCHEMA_FILE=HIPE-2026-data/schemas/hipe-2026-data.schema.json`

You can override them inline, for example:

```bash
remake evaluate-baseline \
  OUTPUT_JSONL=outputs/predictions.de.jsonl \
  GOLD_JSONL=HIPE-2026-data/data/newspapers/v1.0/HIPE-2026-v1.0-impresso-train-de.jsonl
```

## Testing

Run the unit tests with:

```bash
remake test
```

The tests use a fake inference backend and do not require `llama-cpp-python` or model files.

## Where To Start Editing

Common modifications:

1. Change the prompt in `prompts/classify_pair.txt`.
2. Change the decoding defaults in `configs/model.example.json` or `src/hipe2026_mistral_baseline/inference.py`.
   On Apple Silicon, GPU offload is automatic by default unless you explicitly set `--n-gpu-layers`.
3. Change the single-pair behavior in `predict_pair()` inside `src/hipe2026_mistral_baseline/run_baseline.py`.
4. Change the fallback labels in `conservative_default_prediction()` inside `src/hipe2026_mistral_baseline/validation.py`.

If you want to add few-shot examples, the simplest path is to edit the prompt template directly.
