# Release Process

This document describes how to prepare a release for the `hipe-2026-llm-baseline`
repository.

This repository is a small research-code baseline, not a packaged production system.
The release unit is a tagged repository snapshot that includes:

- the baseline code under `src/`
- the default prompt in `prompts/`
- the default runtime wiring in `Makefile`
- the package metadata in `pyproject.toml`
- the short release note in `RELEASE.md`
- bundled non-secret test inputs under `data/test/`, when available

The repository does not ship model weights or the HIPE data repo. Releases document
the code, defaults, and instructions needed to reproduce a run locally.
Generated run artifacts under `results-train.d/`, `results-test.d/`, `hf.d/`, and
model files are not part of `main` releases.

## Release Style

Use simple semantic versions for releases and keep the same version string in:

- `pyproject.toml`
- `RELEASE.md`
- the git tag
- the GitHub release title, if you publish one

Examples:

- `0.1.0`
- `0.1.1`
- `0.2.0`

Recommended git tag format:

```text
v0.1.0
```

## Normal Workflow

1. Prepare release changes on a branch.
2. Update the version and release note.
3. Run local verification.
4. Merge to `main`.
5. Create an annotated tag from the merged commit.
6. Optionally publish a GitHub release.
7. If needed, archive generated result files on a separate archive branch.

## Prepare the Release

### 1. Review the Changes

Inspect the diff since the previous release:

```bash
git log <previous-tag>..HEAD --oneline
git diff <previous-tag>..HEAD --stat
git diff <previous-tag>..HEAD --name-status
```

Pay particular attention to:

- `src/hipe2026_mistral_baseline/`
- `prompts/classify_pair.txt`
- `Makefile`
- `README.md`
- `pyproject.toml`
- `RELEASE.md`
- `tests/`
- `data/test/`

For a patch release that only adds test data or output wiring, confirm explicitly
that the prompt and model behavior did not change:

```bash
git diff <previous-tag>..HEAD -- prompts/classify_pair.txt
git diff <previous-tag>..HEAD -- src/hipe2026_mistral_baseline/inference.py
```

### 2. Update the Version

Update the package version in `pyproject.toml`.

Example:

```toml
[project]
version = "0.1.1"
```

This repository does not maintain a separate changelog, so the main versioned release
metadata lives in:

- `pyproject.toml`
- `RELEASE.md`

### 3. Update `RELEASE.md`

Edit `RELEASE.md` so it describes the current release instead of the previous one.

Keep it short and specific:

- release number
- what changed
- important defaults
- anything users should know about setup or runtime behavior

### 4. Review Documentation

Update documentation when the release changes:

- default model source
- default Hugging Face filename
- inference defaults such as `flash_attn`
- logging behavior
- setup commands
- Makefile targets
- expected data paths under `HIPE-2026-data/`
- bundled test-data paths under `data/test/`
- generated output names under `results-train.d/` and `results-test.d/`
- run config JSON files, named like `baseline_<input-stem>_run1.config.json`

In practice, that usually means reviewing:

- `README.md`
- `RELEASE.md`
- `Makefile`

## Local Verification

Use the project `venv/` and the repository Makefile.

Recommended release checks:

```bash
python3 -m py_compile src/hipe2026_mistral_baseline/*.py scripts/*.py tests/*.py
make test
```

If you changed setup or scorer wiring, also verify:

```bash
make -n setup
make -n run-baseline
make -n evaluate-baseline
```

If you changed the help text or Makefile defaults, also check:

```bash
make
```

If you changed test-data handling or result naming, also check:

```bash
make -n world-test TEST_INPUT_DIR=data/test
```

This should write test outputs using the shared-task style:

```text
results-test.d/baseline_<input-stem>_run1.jsonl
results-test.d/baseline_<input-stem>_run1.config.json
```

If test JSONL files are included, validate them line by line:

```bash
python3 -c 'import json, pathlib; [json.loads(line) for path in pathlib.Path("data/test").glob("*.jsonl") for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]'
```

If you changed the actual inference path, it is useful to run at least one small real
baseline command locally, but that is optional because it depends on:

- a working local `venv`
- the `HIPE-2026-data/` checkout
- a local or downloadable GGUF model
- available hardware

Example:

```bash
make run-baseline RUN_BASELINE_ARGS='--max-docs 1'
```

## Release Checklist

Before tagging, confirm all of the following:

- the working tree is clean
- `pyproject.toml` version is updated
- `RELEASE.md` matches the intended release
- `README.md` reflects current defaults
- `python3 -m py_compile ...` passes
- `make test` passes
- any changed Makefile wiring looks correct with `make -n`
- test output names follow `baseline_<input-stem>_run<run-number>.jsonl`
- each generated prediction file has a neighboring `.config.json` with
  project-relative paths only
- generated `results-*.d/` files are not tracked on `main`

Useful commands:

```bash
git status --short
git diff --stat origin/main..HEAD
git log --oneline origin/main..HEAD
```

## Tagging

After the release branch is merged to `main`, sync your local branch and create an
annotated tag:

```bash
git checkout main
git pull --ff-only
git tag -a v0.1.1 -m "Release 0.1.1"
git push origin v0.1.1
```

Use the actual release version instead of `0.1.1`.

## GitHub Release

The tagged commit is the actual repository release snapshot.

A GitHub release is optional. If you publish one, use:

- tag: `vX.Y.Z`
- title: `Release X.Y.Z`
- body: based on `RELEASE.md`

The GitHub release should describe the same repository state as:

- the git tag
- `pyproject.toml`
- `RELEASE.md`

You can create the GitHub release either in the GitHub web UI or with the GitHub CLI.
The `gh` tool is convenient, but it is not required by this process.

Use only the matching release section from `RELEASE.md` as the body. For example:

```bash
awk '/^# Release 0\.1\.0/{exit} {print}' RELEASE.md > /tmp/hipe-release-v0.1.1.md
gh release create v0.1.1 --title "Release 0.1.1" --notes-file /tmp/hipe-release-v0.1.1.md
```

Use the actual release version instead of `0.1.1`.

If the release already exists, inspect before editing:

```bash
gh release view v0.1.1
```

## Archiving Result Files

Prediction, debug, diagnostic, and run-config outputs should not be committed to
`main`. If result artifacts need to be preserved for documentation, create an
archive branch from the release tag or `main`.

Recommended branch name:

```text
archive/baseline-vX.Y.Z-results
```

Workflow:

```bash
git switch main
git pull --ff-only
git switch -c archive/baseline-vX.Y.Z-results
git add -f results-test.d/
git commit -m "Archive baseline vX.Y.Z test results"
git push -u origin archive/baseline-vX.Y.Z-results
git switch main
git ls-files results-test.d
```

The final `git ls-files results-test.d` should print nothing on `main`.

## Hotfix Releases

For a small hotfix:

1. branch from the release branch or `main`
2. make the minimal fix
3. bump the patch version
4. update `RELEASE.md`
5. rerun verification
6. merge and tag

Example progression:

- `0.1.0`
- `0.1.1`

## Notes Specific to This Repository

- Do not vendor the `HIPE-2026-data` repository into the release. The repo is expected
  to be cloned separately by `make setup`.
- Do not commit model files or Hugging Face cache contents.
- Do not commit generated `results-train.d/`, `results-test.d/`, or `results.d/`
  outputs to `main`; use an archive branch for those files.
- Keep generated run configuration paths project-relative. Avoid absolute local
  paths such as `/Users/.../hipe-2026-llm-baseline/...`.
- Keep the baseline easy to modify. If a release adds complexity, document the reason
  clearly in `README.md` and `RELEASE.md`.
- Prefer keeping the release process lightweight. This is research code, so the main
  goal is a clean, reproducible tagged snapshot rather than a heavy packaging pipeline.
