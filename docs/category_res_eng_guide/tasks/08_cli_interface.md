# Task 8: CLI Interface

**Status**: 🔒 Blocked (depends on Tasks 4-7)  
**Estimated Time**: 3-4 hours  
**Dependencies**: Task 4 (Agent), Task 5 (Analyzer), Task 6 (Extractor), Task 7 (Blueprint Generator)  
**Priority**: Medium-High

---

## 📋 Objective

Build a polished Click-based command-line interface that triggers the category extraction workflow, communicates progress using Rich, handles options for retailer/site/headless mode, and surfaces errors with actionable guidance.

## 🎯 Success Criteria

- [ ] `src/ai_agents/category_extractor/cli.py` created or updated per spec
- [ ] CLI command `poetry run python -m src.ai_agents.category_extractor.cli extract --url ... --retailer-id ...` works
- [ ] Supports `--headless/--no-headless`, `--force-refresh`, and optional `--blueprint-only` flag
- [ ] Displays progress (Rich status / console logging) for major stages
- [ ] Prints summary of categories saved + blueprint path on success
- [ ] Handles exceptions gracefully, outputs helpful error messages, non-zero exit code on failure
- [ ] Includes `main()` entrypoint for packaging

## 📝 Specifications

### File: `src/ai_agents/category_extractor/cli.py`

```python
"""CLI entrypoint for the AI Category Extractor."""
from __future__ import annotations

import asyncio
import sys
from typing import Optional

import click
from rich.console import Console
from rich.panel import Panel
from rich.progress import Progress, SpinnerColumn, TextColumn

from .agent import CategoryExtractionAgent
from .errors import ExtractorError
from .utils.logger import log

console = Console()


@click.group(context_settings={"help_option_names": ["-h", "--help"]})
def cli() -> None:
    """AI-powered category extraction commands."""


@cli.command(name="extract")
@click.option("--url", required=True, help="Website URL to extract categories from")
@click.option("--retailer-id", required=True, type=int, help="Retailer ID in the database")
@click.option("--headless/--no-headless", default=True, help="Run browser in headless mode")
@click.option("--force-refresh", is_flag=True, help="Force reload of the initial page")
@click.option("--blueprint-only", is_flag=True, help="Generate blueprint without saving categories")
def extract_command(url: str, retailer_id: int, headless: bool, force_refresh: bool, blueprint_only: bool) -> None:
    """Extract categories for the given retailer."""
    try:
        asyncio.run(_run_extract(url, retailer_id, headless, force_refresh, blueprint_only))
    except KeyboardInterrupt:
        console.print("\n[red]Cancelled by user[/red]")
        sys.exit(130)
    except ExtractorError as exc:
        console.print(Panel.fit(str(exc), title="Extraction Failed", border_style="red"))
        sys.exit(1)
    except Exception as exc:  # noqa: BLE001
        log.exception("Unexpected CLI failure")
        console.print(Panel.fit(str(exc), title="Unexpected Error", border_style="red"))
        sys.exit(1)


async def _run_extract(url: str, retailer_id: int, headless: bool, force_refresh: bool, blueprint_only: bool) -> None:
    agent = CategoryExtractionAgent(retailer_id=retailer_id, site_url=url, headless=headless)

    console.print(Panel.fit(f"Retailer [bold]{retailer_id}[/bold]\nURL: [cyan]{url}[/cyan]", title="AI Category Extractor", border_style="blue"))

    with Progress(SpinnerColumn(), TextColumn("{task.description}"), transient=True, console=console) as progress:
        stage = progress.add_task("Bootstrapping...", start=True)

        await agent.initialize_browser()
        progress.update(stage, description="Analyzing navigation...")
        analysis = await agent.page_analyzer.analyze(url, force_refresh)

        progress.update(stage, description="Extracting categories...")
        extraction = await agent.category_extractor.extract(url)

        categories = extraction["categories"]
        stats = extraction["total"]

        if blueprint_only:
            progress.update(stage, description="Generating blueprint (no DB save)...")
            blueprint_path = await agent.blueprint_generator.generate(categories, analysis)
            console.print(_success_panel(stats, blueprint_path, saved=False))
        else:
            progress.update(stage, description="Saving categories...")
            save_stats = await agent.database_tool.persist(categories, retailer_id=retailer_id)

            progress.update(stage, description="Generating blueprint...")
            blueprint_path = await agent.blueprint_generator.generate(categories, analysis)

            console.print(_success_panel(stats, blueprint_path, saved=True, save_stats=save_stats))

    await agent.cleanup()


def _success_panel(total: int, blueprint_path: str, saved: bool, save_stats: Optional[dict] = None) -> Panel:
    lines = [f"Categories discovered: [green]{total}[/green]", f"Blueprint saved to: [cyan]{blueprint_path}[/cyan]"]
    if saved and save_stats:
        lines.insert(1, f"Database -> saved: {save_stats.get('saved', 0)}, updated: {save_stats.get('updated', 0)}")
    return Panel("\n".join(lines), title="Extraction Complete", border_style="green")


def main() -> None:
    """Entrypoint for poetry script hook."""
    cli()


if __name__ == "__main__":
    main()
```

> Adjust options/flags as implementation evolves. Keep CLI output concise but informative. Use Rich panels for readable status reporting.

## 🔧 Implementation Steps

1. **Set up Click group + commands**: Provide `extract` command as described and placeholder for future commands (e.g., blueprint execution).
2. **Integrate Rich progress** to show major stages. Ensure `transient=True` so final summary remains.
3. **Wire agent methods**: Call analyzer, extractor, DB persistence, and blueprint generator in sequence. Honor `--blueprint-only` flag by skipping DB save.
4. **Handle exceptions**: Convert `ExtractorError` subclasses into friendly CLI messaging. Unexpected errors should still log stack trace via Loguru.
5. **Support environment flags**: `--headless/--no-headless` toggles Playwright behavior; `--force-refresh` ensures `page.goto` even if same URL.
6. **Add `main()`** for `poetry run` compatibility and potential console_scripts entry.
7. **Document usage** in `src/ai_agents/category_extractor/README.md` (Task 1 already seeds doc—update if necessary).

## ✅ Validation Checklist

- [ ] `poetry run python -m src.ai_agents.category_extractor.cli --help` shows command + options
- [ ] Running command with mock agent (unit test patching tools) returns success message
- [ ] Non-zero exit code on failure (simulate raising `ExtractorError` from tool)
- [ ] Rich progress output visible in terminal (manually verified)
- [ ] Logging includes CLI invocation details at INFO level

## 🧪 Manual Testing

```bash
poetry run python -m src.ai_agents.category_extractor.cli extract \
    --url https://example.com \
    --retailer-id 1 \
    --no-headless \
    --force-refresh
```

For automated test, patch agent tools and assert CLI prints success summary (use `CliRunner` from Click).

## 📝 Deliverables

1. `cli.py` implementation with Click and Rich integration
2. Unit test(s) using `click.testing.CliRunner`
3. README usage snippet updated if necessary
4. `MASTER_TASKLIST.md` entry updated

## 🚨 Common Issues & Solutions

| Issue | Symptom | Fix |
|-------|---------|-----|
| Event loop reuse errors | `RuntimeError: Event loop is closed` | Run CLI via `asyncio.run` inside command function |
| Rich progress not showing | No spinner/updates | Ensure `with Progress(...)` context wraps awaited operations |
| Headless flag ignored | Browser always headless | Pass `headless` to `CategoryExtractionAgent` constructor |
| CLI command not discoverable | `ModuleNotFoundError` when using `-m` | Ensure `__main__` guard calls `main()` |

## 📚 Next Steps

After completing Task 8:
1. Update `MASTER_TASKLIST.md` status/time.
2. Commit CLI changes + tests.
3. Move to **Task 9: Error Handling & Logging** for consolidating exception/retry strategy.

**Last Updated**: 2025-09-30
