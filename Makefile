ifneq ("$(wildcard .env)","")
include .env
export
endif

.DEFAULT_GOAL := help

PYTHON ?= python3
ENV_FILE ?= .env
DATA_REPO_URL ?= https://github.com/hipe-eval/HIPE-2026-data.git
DATA_REPO_DIR ?= HIPE-2026-data
DATA_REQUIREMENTS ?= $(DATA_REPO_DIR)/requirements.txt
INPUT_JSONL ?= $(DATA_REPO_DIR)/data/newspapers/v1.0/HIPE-2026-v1.0-impresso-train-en.jsonl
OUTPUT_JSONL ?= outputs/predictions.en.jsonl
DEBUG_JSONL ?= outputs/debug.en.jsonl
GOLD_JSONL ?= $(INPUT_JSONL)
SCORER_SCRIPT ?= $(DATA_REPO_DIR)/scripts/file_scorer_evaluation.py
SCHEMA_FILE ?= $(DATA_REPO_DIR)/schemas/hipe-2026-data.schema.json
EN_INPUT_JSONL ?= $(DATA_REPO_DIR)/data/newspapers/v1.0/HIPE-2026-v1.0-impresso-train-en.jsonl
DE_INPUT_JSONL ?= $(DATA_REPO_DIR)/data/newspapers/v1.0/HIPE-2026-v1.0-impresso-train-de.jsonl
FR_INPUT_JSONL ?= $(DATA_REPO_DIR)/data/newspapers/v1.0/HIPE-2026-v1.0-impresso-train-fr.jsonl
EN_OUTPUT_JSONL ?= outputs/predictions.en.jsonl
DE_OUTPUT_JSONL ?= outputs/predictions.de.jsonl
FR_OUTPUT_JSONL ?= outputs/predictions.fr.jsonl
EN_DEBUG_JSONL ?= outputs/debug.en.jsonl
DE_DEBUG_JSONL ?= outputs/debug.de.jsonl
FR_DEBUG_JSONL ?= outputs/debug.fr.jsonl
HF_HOME ?= ./hf.d
HF_REPO ?= mistralai/Ministral-3-3B-Instruct-2512-GGUF
HF_FILENAME ?= Ministral-3-3B-Instruct-2512-Q4_K_M.gguf
RUN_BASELINE_ARGS ?=
EVALUATE_ARGS ?=

.PHONY: help setup init-env install install-data install-data-deps evaluate-baseline evaluate-all-languages clean test

help:
	@echo "HIPE 2026 Mistral Baseline"
	@echo ""
	@echo "Main targets:"
	@echo "  remake setup              Create .env, install package, clone/update HIPE-2026-data, install scorer deps"
	@echo "  remake run-baseline       Run the baseline on INPUT_JSONL"
	@echo "  remake run-all-languages  Run the baseline on EN, DE, and FR"
	@echo "  remake evaluate-baseline  Score OUTPUT_JSONL against GOLD_JSONL"
	@echo "  remake evaluate-all-languages  Score EN, DE, and FR outputs"
	@echo "  remake test               Run the test suite"
	@echo "  remake clean              Remove local caches and generated outputs"
	@echo ""
	@echo "Baseline outputs are file targets: if a prediction file already exists, remake will not rebuild it."
	@echo "Use 'remake clean' or delete specific outputs to force a rerun."
	@echo ""
	@echo "Important variables:"
	@echo "  INPUT_JSONL=$(INPUT_JSONL)"
	@echo "  OUTPUT_JSONL=$(OUTPUT_JSONL)"
	@echo "  DEBUG_JSONL=$(DEBUG_JSONL)"
	@echo "  HF_HOME=$(HF_HOME)"
	@echo "  HF_REPO=$(HF_REPO)"
	@echo "  HF_FILENAME=$(HF_FILENAME)"
	@echo ""
	@echo "Examples:"
	@echo "  remake setup"
	@echo "  remake run-baseline"
	@echo "  remake evaluate-baseline"
	@echo "  remake run-baseline INPUT_JSONL=$(DATA_REPO_DIR)/data/newspapers/v1.0/HIPE-2026-v1.0-impresso-train-de.jsonl OUTPUT_JSONL=outputs/predictions.de.jsonl DEBUG_JSONL=outputs/debug.de.jsonl"

setup: init-env install install-data install-data-deps

init-env:
	@if [ ! -f "$(ENV_FILE)" ]; then \
		printf "HF_HOME=./hf.d\n" > "$(ENV_FILE)"; \
		echo "Created $(ENV_FILE)"; \
	elif ! grep -q '^HF_HOME=' "$(ENV_FILE)"; then \
		printf "\nHF_HOME=./hf.d\n" >> "$(ENV_FILE)"; \
		echo "Added HF_HOME to $(ENV_FILE)"; \
	else \
		echo "$(ENV_FILE) already contains HF_HOME"; \
	fi

install:
	$(PYTHON) -m pip install -e .

install-data:
	@if [ -d "$(DATA_REPO_DIR)/.git" ]; then \
		echo "Updating $(DATA_REPO_DIR)"; \
		git -C "$(DATA_REPO_DIR)" pull --ff-only; \
	else \
		echo "Cloning $(DATA_REPO_URL) into $(DATA_REPO_DIR)"; \
		git clone --depth 1 "$(DATA_REPO_URL)" "$(DATA_REPO_DIR)"; \
	fi

install-data-deps:
	@if [ -f "$(DATA_REQUIREMENTS)" ]; then \
		$(PYTHON) -m pip install -r "$(DATA_REQUIREMENTS)"; \
	else \
		echo "Missing $(DATA_REQUIREMENTS). Run 'remake install-data' first."; \
		exit 1; \
	fi

$(OUTPUT_JSONL):
	HF_HOME="$(HF_HOME)" $(PYTHON) scripts/run_baseline.py \
		--input-jsonl "$(INPUT_JSONL)" \
		--output-jsonl "$(OUTPUT_JSONL)" \
		--debug-jsonl "$(DEBUG_JSONL)" \
		--hf-repo "$(HF_REPO)" \
		--hf-filename "$(HF_FILENAME)" \
		$(RUN_BASELINE_ARGS)

run-baseline: $(OUTPUT_JSONL)

run-all-languages:
	$(MAKE) run-baseline INPUT_JSONL="$(EN_INPUT_JSONL)" OUTPUT_JSONL="$(EN_OUTPUT_JSONL)" DEBUG_JSONL="$(EN_DEBUG_JSONL)"
	$(MAKE) run-baseline INPUT_JSONL="$(DE_INPUT_JSONL)" OUTPUT_JSONL="$(DE_OUTPUT_JSONL)" DEBUG_JSONL="$(DE_DEBUG_JSONL)"
	$(MAKE) run-baseline INPUT_JSONL="$(FR_INPUT_JSONL)" OUTPUT_JSONL="$(FR_OUTPUT_JSONL)" DEBUG_JSONL="$(FR_DEBUG_JSONL)"

evaluate-baseline: install-data-deps
	$(PYTHON) scripts/evaluate_predictions.py \
		--scorer-script "$(SCORER_SCRIPT)" \
		--schema-file "$(SCHEMA_FILE)" \
		--gold-jsonl "$(GOLD_JSONL)" \
		--predictions-jsonl "$(OUTPUT_JSONL)" \
		$(EVALUATE_ARGS)

evaluate-all-languages: install-data-deps
	$(MAKE) evaluate-baseline OUTPUT_JSONL="$(EN_OUTPUT_JSONL)" GOLD_JSONL="$(EN_INPUT_JSONL)"
	$(MAKE) evaluate-baseline OUTPUT_JSONL="$(DE_OUTPUT_JSONL)" GOLD_JSONL="$(DE_INPUT_JSONL)"
	$(MAKE) evaluate-baseline OUTPUT_JSONL="$(FR_OUTPUT_JSONL)" GOLD_JSONL="$(FR_INPUT_JSONL)"

clean:
	rm -rf .pytest_cache
	rm -rf hf.d
	rm -rf src/*.egg-info
	find . -type d -name "__pycache__" -prune -exec rm -rf {} +
	find . -type f -name "*.pyc" -delete
	find outputs -type f ! -name "README.md" -delete

test:
	$(PYTHON) -m unittest discover -s tests -p "test_*.py"
