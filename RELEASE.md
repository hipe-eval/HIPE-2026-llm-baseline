# Release 0.1.0

Initial research baseline release for HIPE 2026 person-place relation qualification.

## Included

- local prompt-based baseline using `llama-cpp-python`
- scorer-compatible reading and writing of the official HIPE 2026 JSONL format
- pairwise classification over provided `sampled_pairs`
- one prompt template with deterministic decoding defaults
- strict JSON parsing, validation, and conservative fallback behavior
- small test suite with fake inference for smoke testing

## Repository shape

- simple research-code layout
- runnable default path without config
- optional small JSON config for model and decoding defaults
- thin wrapper for calling the official scorer from a local checkout

## Current defaults

- model family target: `mistralai/Ministral-3-3B-Instruct-2512`
- decoder: `llama-cpp-python`
- labels:
  - `at`: `TRUE`, `PROBABLE`, `FALSE`
  - `isAt`: `TRUE`, `FALSE`

## Notes

- this release follows the public HIPE 2026 schema based on document-level `sampled_pairs`
- real model weights are not included in the repository
- intended as a minimal starting point for participants to modify easily
