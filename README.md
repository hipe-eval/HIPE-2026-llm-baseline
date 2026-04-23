# HIPE 2026 Mistral Baseline

Minimal local baseline for the HIPE 2026 CLEF task on person-place relation qualification.

This repo is intentionally small and closer to research code than framework code.

This baseline:

- runs fully locally
- uses `llama-cpp-python` with a GGUF model
- is built around one prompt template and deterministic decoding
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

## Layout

```text
.
├── Makefile
├── configs/
│   └── model.example.json
├── data/
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
pip install -e .
```

Project conventions:

- put input JSONL files under `data/`
- put local GGUF files under `models/`
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
python scripts/run_baseline.py \
  --input-jsonl data/HIPE-2026-v1.0-impresso-train-en.jsonl \
  --output-jsonl outputs/predictions.en.jsonl \
  --debug-jsonl outputs/debug.en.jsonl \
  --model-path models/ministral-q4_k_m.gguf
```

This no-config path is the default intended workflow.

If you want a small amount of reusable configuration, you can optionally pass a
JSON config file for model, prompt, and decoding defaults:

```bash
python scripts/run_baseline.py \
  --config configs/model.example.json \
  --input-jsonl data/HIPE-2026-v1.0-impresso-train-en.jsonl \
  --output-jsonl outputs/predictions.en.jsonl
```

CLI flags override config values, so the simplest pattern is:

- keep your usual model setup in `configs/model.example.json`
- override only the input and output files on each run

Or resolve a GGUF file from Hugging Face:

```bash
python scripts/run_baseline.py \
  --input-jsonl /path/to/input.jsonl \
  --output-jsonl /path/to/predictions.jsonl \
  --hf-repo mistralai/Ministral-3-3B-Instruct-2512-GGUF \
  --hf-filename Ministral-3-3B-Instruct-2512-Q4_K_M.gguf
```

## Evaluation

If you have a local checkout of the official HIPE 2026 data repo, use the helper wrapper:

```bash
python scripts/evaluate_predictions.py \
  --scorer-script /path/to/HIPE-2026-data/scripts/file_scorer_evaluation.py \
  --schema-file /path/to/HIPE-2026-data/schemas/hipe-2026-data.schema.json \
  --gold-jsonl /path/to/gold.jsonl \
  --predictions-jsonl outputs/predictions.en.jsonl
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
3. Change the single-pair behavior in `predict_pair()` inside `src/hipe2026_mistral_baseline/run_baseline.py`.
4. Change the fallback labels in `conservative_default_prediction()` inside `src/hipe2026_mistral_baseline/validation.py`.

If you want to add few-shot examples, the simplest path is to edit the prompt template directly.
