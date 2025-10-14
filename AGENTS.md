# Repository Guidelines

## Project Structure & Module Organization
The agent lives under `cdbai/` and exposes `cdbai_chat(prompt)` for programmatic use. The CLI wrapper `run_code.py` simply calls that function. Supporting scripts (`normalize_prompt.py`, `load_cdbai_column_descriptions.py`) remain at repo root, while static resources ship inside `cdbai/data/` (e.g., `id_mapping.csv`). Generated artifacts (code, prompt snapshots, CSV exports, plots, JSON results) are written to `output/` during each run.

## Build, Test, and Development Commands
Install dependencies locally via `uv pip install -e .`. The CLI usage mirrors production: `UV_CACHE_DIR=.uv_cache uv run run_code.py --prompt "<prompt>"`. Unit tests use stubbed dependencies: `python -m unittest discover tests`. When running locally, ensure required env vars are exported (Google project/dataset/table, AWS bucket/region, `SMART_LLM`, `FAST_LLM`, `LITELLM_PROXY_API_BASE`).

## Coding Style & Naming Conventions
Target Python 3.10+, 4-space indentation, PEP 8 naming. Pipeline functions include docstrings with Args/Returns sections—match that style. Keep configuration in CONSTANT_CASE at module top and ensure new helpers stay import-friendly (no side-effects at import time). Plot helpers must use `allocate_plot_png_path()` (and `allocate_plot_svg_path(png_path)`) so artefact names stay aligned.

## Testing Guidelines
Tests rely on stubs (pandas, litellm, boto3). Avoid asserting brittle numeric results; focus on links, prompt handling, and error formatting. Clean up any files created under `output/` during tests (the harness already prefixes outputs with `test_`). Before deploying changes, run `python -m unittest discover tests` and (optionally) a live CLI run against a staging project.

## Commit & Pull Request Guidelines
Use clear imperative commit titles (e.g., `feat: expose cdbai_chat helper`). Include context on schema/SQL changes, sample CLI invocation, and any new env vars. When plots change, attach images; otherwise share the relevant S3 URLs or CSV diffs. Reference associated tickets to keep traceability.

## Security & Configuration Tips
Never commit secrets. Keep `GOOGLE_APPLICATION_CREDENTIALS` and AWS keys in local `.env` files. Artifact uploads go to `https://s3.<region>.amazonaws.com/<bucket>/...`; confirm buckets are access-controlled. If a prompt includes sensitive terms, sanitize before sharing logs. Rotate Fast/Smart LLM credentials promptly if compromised.
