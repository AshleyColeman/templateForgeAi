# TemplateForge AI - AI Category Extractor

This repository hosts the implementation of an AI-powered category extraction agent. To get started, follow the task specifications under `docs/category_res_eng_guide/tasks/` beginning with Task 1.

## Quickstart

```bash
poetry install
poetry run playwright install chromium
poetry run python verify_setup.py
```

All environment variables are documented in `.env.example`.

## Quality Checks

```bash
make quality
```

This runs formatting, linting, and tests (excluding e2e). To include end-to-end checks, set `RUN_E2E=1` and invoke the relevant pytest markers once Playwright, PostgreSQL, and Bedrock credentials are available.
