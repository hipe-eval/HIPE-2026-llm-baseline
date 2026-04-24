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
DATASET_SPLIT ?= train
DATASET_OUTPUT_TAG ?= $(if $(filter train,$(DATASET_SPLIT)),,$(DATASET_SPLIT).)
ENABLE_EVAL ?= $(if $(filter train,$(DATASET_SPLIT)),1,0)
ENABLE_DIAGNOSTICS ?= $(if $(filter train,$(DATASET_SPLIT)),1,0)
RESULTS_DIR ?= results.d
INPUT_JSONL ?= $(DATA_REPO_DIR)/data/newspapers/v1.0/HIPE-2026-v1.0-impresso-$(DATASET_SPLIT)-en.jsonl
OUTPUT_JSONL ?= $(RESULTS_DIR)/predictions.$(DATASET_OUTPUT_TAG)en.jsonl
DEBUG_JSONL ?= $(RESULTS_DIR)/debug.$(DATASET_OUTPUT_TAG)en.jsonl
GOLD_JSONL ?= $(INPUT_JSONL)
DIAGNOSTIC_JSON ?= $(RESULTS_DIR)/predictions.$(DATASET_OUTPUT_TAG)en.diagnostic.json
SCORER_SCRIPT ?= $(DATA_REPO_DIR)/scripts/file_scorer_evaluation.py
SCHEMA_FILE ?= $(DATA_REPO_DIR)/schemas/hipe-2026-data.schema.json
EN_INPUT_JSONL ?= $(DATA_REPO_DIR)/data/newspapers/v1.0/HIPE-2026-v1.0-impresso-$(DATASET_SPLIT)-en.jsonl
DE_INPUT_JSONL ?= $(DATA_REPO_DIR)/data/newspapers/v1.0/HIPE-2026-v1.0-impresso-$(DATASET_SPLIT)-de.jsonl
FR_INPUT_JSONL ?= $(DATA_REPO_DIR)/data/newspapers/v1.0/HIPE-2026-v1.0-impresso-$(DATASET_SPLIT)-fr.jsonl
TEST_EN_INPUT_JSONL ?= $(DATA_REPO_DIR)/data/newspapers/v1.0/HIPE-2026-v1.0-impresso-test-en.jsonl
TEST_DE_INPUT_JSONL ?= $(DATA_REPO_DIR)/data/newspapers/v1.0/HIPE-2026-v1.0-impresso-test-de.jsonl
TEST_FR_INPUT_JSONL ?= $(DATA_REPO_DIR)/data/newspapers/v1.0/HIPE-2026-v1.0-impresso-test-fr.jsonl
EN_OUTPUT_JSONL ?= $(RESULTS_DIR)/predictions.$(DATASET_OUTPUT_TAG)en.jsonl
DE_OUTPUT_JSONL ?= $(RESULTS_DIR)/predictions.$(DATASET_OUTPUT_TAG)de.jsonl
FR_OUTPUT_JSONL ?= $(RESULTS_DIR)/predictions.$(DATASET_OUTPUT_TAG)fr.jsonl
TEST_EN_OUTPUT_JSONL ?= $(RESULTS_DIR)/predictions.test.en.jsonl
TEST_DE_OUTPUT_JSONL ?= $(RESULTS_DIR)/predictions.test.de.jsonl
TEST_FR_OUTPUT_JSONL ?= $(RESULTS_DIR)/predictions.test.fr.jsonl
EN_DIAGNOSTIC_JSON ?= $(RESULTS_DIR)/predictions.$(DATASET_OUTPUT_TAG)en.diagnostic.json
DE_DIAGNOSTIC_JSON ?= $(RESULTS_DIR)/predictions.$(DATASET_OUTPUT_TAG)de.diagnostic.json
FR_DIAGNOSTIC_JSON ?= $(RESULTS_DIR)/predictions.$(DATASET_OUTPUT_TAG)fr.diagnostic.json
EN_DEBUG_JSONL ?= $(RESULTS_DIR)/debug.$(DATASET_OUTPUT_TAG)en.jsonl
DE_DEBUG_JSONL ?= $(RESULTS_DIR)/debug.$(DATASET_OUTPUT_TAG)de.jsonl
FR_DEBUG_JSONL ?= $(RESULTS_DIR)/debug.$(DATASET_OUTPUT_TAG)fr.jsonl
TEST_EN_DEBUG_JSONL ?= $(RESULTS_DIR)/debug.test.en.jsonl
TEST_DE_DEBUG_JSONL ?= $(RESULTS_DIR)/debug.test.de.jsonl
TEST_FR_DEBUG_JSONL ?= $(RESULTS_DIR)/debug.test.fr.jsonl
HF_HOME ?= ./hf.d
HF_REPO ?= mistralai/Ministral-3-3B-Instruct-2512-GGUF
HF_FILENAME ?= Ministral-3-3B-Instruct-2512-Q4_K_M.gguf
RUN_BASELINE_ARGS ?=
EVALUATE_ARGS ?=
DIAGNOSTIC_ARGS ?=

# CUDA wheel index for llama-cpp-python. Override LLAMA_CPP_CUDA_INDEX to match
# your CUDA toolkit (cu121, cu122, cu123, cu124). Default targets cu124.
LLAMA_CPP_CUDA_INDEX ?= https://abetlen.github.io/llama-cpp-python/whl/cu124

.PHONY: help setup init-env install install-data install-data-deps evaluate-baseline evaluate-all-languages diagnose-baseline diagnose-all-languages world world-test clean test

help:
	@echo "HIPE 2026 Mistral Baseline"
	@echo ""
	@echo "Main targets:"
	@echo "  remake setup              Create .env, install package, clone/update HIPE-2026-data, install scorer deps"
	@echo "  remake world              Run baselines, and when enabled also evaluate outputs and build diagnostics"
	@echo "  remake world-test         Run baselines on the released test split without evaluation"
	@echo "  remake run-baseline       Run the baseline on INPUT_JSONL"
	@echo "  remake run-all-languages  Run the baseline on EN, DE, and FR"
	@echo "  remake evaluate-baseline  Score OUTPUT_JSONL against GOLD_JSONL"
	@echo "  remake evaluate-all-languages  Score EN, DE, and FR outputs"
	@echo "  remake diagnose-baseline  Merge GOLD_JSONL and OUTPUT_JSONL into DIAGNOSTIC_JSON"
	@echo "  remake diagnose-all-languages  Build EN, DE, and FR diagnostic JSON files"
	@echo "  remake test               Run the test suite"
	@echo "  remake clean              Remove local caches and generated outputs"
	@echo ""
	@echo "Baseline outputs are file targets: if a prediction file already exists, remake will not rebuild it."
	@echo "Use 'remake clean' or delete specific outputs to force a rerun."
	@echo ""
	@echo "Important variables:"
	@echo "  DATASET_SPLIT=$(DATASET_SPLIT)"
	@echo "  INPUT_JSONL=$(INPUT_JSONL)"
	@echo "  RESULTS_DIR=$(RESULTS_DIR)"
	@echo "  OUTPUT_JSONL=$(OUTPUT_JSONL)"
	@echo "  DEBUG_JSONL=$(DEBUG_JSONL)"
	@echo "  DIAGNOSTIC_JSON=$(DIAGNOSTIC_JSON)"
	@echo "  ENABLE_EVAL=$(ENABLE_EVAL)"
	@echo "  ENABLE_DIAGNOSTICS=$(ENABLE_DIAGNOSTICS)"
	@echo "  HF_HOME=$(HF_HOME)"
	@echo "  HF_REPO=$(HF_REPO)"
	@echo "  HF_FILENAME=$(HF_FILENAME)"
	@echo ""
	@echo "Examples:"
	@echo "  remake setup"
	@echo "  remake world"
	@echo "  remake world-test"
	@echo "  remake run-baseline"
	@echo "  remake evaluate-baseline"
	@echo "  remake diagnose-baseline"
	@echo "  remake run-baseline INPUT_JSONL=$(DATA_REPO_DIR)/data/newspapers/v1.0/HIPE-2026-v1.0-impresso-train-de.jsonl OUTPUT_JSONL=$(RESULTS_DIR)/predictions.de.jsonl DEBUG_JSONL=$(RESULTS_DIR)/debug.de.jsonl"

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
	@if command -v nvidia-smi >/dev/null 2>&1; then \
		echo "NVIDIA GPU detected, installing CUDA build of llama-cpp-python from $(LLAMA_CPP_CUDA_INDEX)"; \
		$(PYTHON) -m pip install llama-cpp-python \
			--extra-index-url "$(LLAMA_CPP_CUDA_INDEX)" \
			--force-reinstall --no-cache-dir --upgrade; \
	else \
		echo "No NVIDIA GPU detected, keeping default llama-cpp-python (CPU / Metal on macOS)"; \
	fi

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

$(DIAGNOSTIC_JSON): $(OUTPUT_JSONL)
	$(PYTHON) scripts/compare_predictions.py \
		--gold-jsonl "$(GOLD_JSONL)" \
		--predictions-jsonl "$(OUTPUT_JSONL)" \
		--output-json "$(DIAGNOSTIC_JSON)" \
		$(DIAGNOSTIC_ARGS)

diagnose-baseline: $(DIAGNOSTIC_JSON)

diagnose-all-languages:
	$(MAKE) diagnose-baseline INPUT_JSONL="$(EN_INPUT_JSONL)" OUTPUT_JSONL="$(EN_OUTPUT_JSONL)" DEBUG_JSONL="$(EN_DEBUG_JSONL)" GOLD_JSONL="$(EN_INPUT_JSONL)" DIAGNOSTIC_JSON="$(EN_DIAGNOSTIC_JSON)"
	$(MAKE) diagnose-baseline INPUT_JSONL="$(DE_INPUT_JSONL)" OUTPUT_JSONL="$(DE_OUTPUT_JSONL)" DEBUG_JSONL="$(DE_DEBUG_JSONL)" GOLD_JSONL="$(DE_INPUT_JSONL)" DIAGNOSTIC_JSON="$(DE_DIAGNOSTIC_JSON)"
	$(MAKE) diagnose-baseline INPUT_JSONL="$(FR_INPUT_JSONL)" OUTPUT_JSONL="$(FR_OUTPUT_JSONL)" DEBUG_JSONL="$(FR_DEBUG_JSONL)" GOLD_JSONL="$(FR_INPUT_JSONL)" DIAGNOSTIC_JSON="$(FR_DIAGNOSTIC_JSON)"

world: run-all-languages
ifeq ($(ENABLE_EVAL),1)
	$(MAKE) evaluate-all-languages
endif
ifeq ($(ENABLE_DIAGNOSTICS),1)
	$(MAKE) diagnose-all-languages
endif

world-test:
	$(MAKE) run-all-languages \
		EN_INPUT_JSONL="$(TEST_EN_INPUT_JSONL)" \
		DE_INPUT_JSONL="$(TEST_DE_INPUT_JSONL)" \
		FR_INPUT_JSONL="$(TEST_FR_INPUT_JSONL)" \
		EN_OUTPUT_JSONL="$(TEST_EN_OUTPUT_JSONL)" \
		DE_OUTPUT_JSONL="$(TEST_DE_OUTPUT_JSONL)" \
		FR_OUTPUT_JSONL="$(TEST_FR_OUTPUT_JSONL)" \
		EN_DEBUG_JSONL="$(TEST_EN_DEBUG_JSONL)" \
		DE_DEBUG_JSONL="$(TEST_DE_DEBUG_JSONL)" \
		FR_DEBUG_JSONL="$(TEST_FR_DEBUG_JSONL)"

clean:
	rm -rf .pytest_cache
	rm -rf hf.d
	rm -rf $(RESULTS_DIR)
	rm -rf src/*.egg-info
	find . -type d -name "__pycache__" -prune -exec rm -rf {} +
	find . -type f -name "*.pyc" -delete
	find outputs -type f ! -name "README.md" -delete

test:
	$(PYTHON) -m unittest discover -s tests -p "test_*.py"
