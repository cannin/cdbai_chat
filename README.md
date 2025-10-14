# Google BigQuery Agent

This project wraps the drug response/-omics analysis workflow into an importable package that can also be launched from the command line. The agent takes a natural-language prompt, uses an LLM once to emit executable Python that embeds the exact BigQuery SQL, executes the query, and uploads all run artifacts (code, CSV, plots, JSON) to S3.

## Requirements

- Python 3.10+
- Environment variables providing credentials and configuration:
  - `GOOGLE_PROJECT_ID`, `GOOGLE_DATASET`, `GOOGLE_TABLE`
  - `GOOGLE_APPLICATION_CREDENTIALS`
  - `AWS_S3_BUCKET`, `AWS_DEFAULT_REGION`
  - `LITELLM_PROXY_API_BASE`
  - `SMART_LLM` (defaults to `azure/gpt-5`) – generates the analysis code
  - `FAST_LLM` (defaults to `azure/gpt-4o-mini`) – optional spell-check in the prompt stage

Install dependencies via `uv pip install -e .` (or your preferred tool reading `pyproject.toml`).

## Command-Line Usage

```
uv run run_code.py --prompt "calculate the correlation of tp53 vs mdm2 expression in ccle"
```

The command prints a JSON result and writes artifacts to `output/`. Returned JSON also contains HTTPS links to the uploaded code/CSV files.

## Importable API

```python
from cdbai import run_pipeline

result = run_pipeline("calculate the correlation of tp53 vs mdm2 expression in ccle")
print(result)
```

The dictionary matches the CLI output (keys include `type`, `value`, `normalized_prompt`, `code`, `csv`, etc.).

## Tests

Run `python -m unittest discover tests` to execute the stubbed unit tests. Tests auto-prefix artifacts with `test_` and clean them up.

## Notes

- The LLM-generated code is saved to `output/tmp_<timestamp>.py` before execution for traceability.
- Any error response includes the exact SQL statement and Python code that produced it.
- Plots should obtain filenames via `allocate_plot_png_path()` and the matching SVG via `allocate_plot_svg_path(png_path)` before uploading to S3.
