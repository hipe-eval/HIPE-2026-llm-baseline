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

The repository does not ship model weights or the HIPE data repo. Releases document
the code, defaults, and instructions needed to reproduce a run locally.

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
6. Publish a GitHub release if needed.

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

In practice, that usually means reviewing:

- `README.md`
- `RELEASE.md`
- `Makefile`

## Local Verification

Use the project `venv/` and `remake`, not the system `make`.

Recommended release checks:

```bash
python3 -m py_compile src/hipe2026_mistral_baseline/*.py scripts/*.py tests/*.py
remake test
```

If you changed setup or scorer wiring, also verify:

```bash
remake -n setup
remake -n run-baseline
remake -n evaluate-baseline
```

If you changed the help text or Makefile defaults, also check:

```bash
remake
```

If you changed the actual inference path, it is useful to run at least one small real
baseline command locally, but that is optional because it depends on:

- a working local `venv`
- the `HIPE-2026-data/` checkout
- a local or downloadable GGUF model
- available hardware

Example:

```bash
remake run-baseline RUN_BASELINE_ARGS='--max-docs 1'
```

## Release Checklist

Before tagging, confirm all of the following:

- the working tree is clean
- `pyproject.toml` version is updated
- `RELEASE.md` matches the intended release
- `README.md` reflects current defaults
- `python3 -m py_compile ...` passes
- `remake test` passes
- any changed Makefile wiring looks correct with `remake -n`

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

If you publish a GitHub release, use:

- tag: `vX.Y.Z`
- title: `Release X.Y.Z`
- body: based on `RELEASE.md`

The GitHub release should describe the same repository state as:

- the git tag
- `pyproject.toml`
- `RELEASE.md`

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
  to be cloned separately by `remake setup`.
- Do not commit model files or Hugging Face cache contents.
- Keep the baseline easy to modify. If a release adds complexity, document the reason
  clearly in `README.md` and `RELEASE.md`.
- Prefer keeping the release process lightweight. This is research code, so the main
  goal is a clean, reproducible tagged snapshot rather than a heavy packaging pipeline.
