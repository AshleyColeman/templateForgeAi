# AI Category Extractor

Autonomous AI agent for extracting product categories from e-commerce websites.

## Installation

```bash
poetry install
poetry run playwright install chromium
```

## Configuration

Copy `.env.example` to `.env` and fill in your credentials.

## Usage

```bash
poetry run python -m src.ai_agents.category_extractor.cli extract \
    --url https://example.com \
    --retailer-id 1
```

## Development

Implementation tasks live in `docs/category_res_eng_guide/tasks/`. Complete them sequentially for best results.
