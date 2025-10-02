"""CLI entrypoint for the AI category extractor."""
from __future__ import annotations

import asyncio
import logging
import sys
from typing import Optional

import click
from rich.console import Console
from rich.panel import Panel
from rich.progress import Progress, SpinnerColumn, TextColumn

from .agent import CategoryExtractionAgent
from .blueprints.executor import execute_blueprint
from .blueprints.loader import load_blueprint
from .errors import ExtractorError

console = Console()

# Enable Strands logging for debugging
logging.basicConfig(
    level=logging.DEBUG,
    format="%(levelname)s | %(name)s | %(message)s",
    handlers=[logging.StreamHandler()]
)
logging.getLogger("strands").setLevel(logging.DEBUG)


@click.group(context_settings={"help_option_names": ["-h", "--help"]})
def cli() -> None:
    """AI-powered category extraction commands."""


@cli.command(name="extract")
@click.option("--url", required=True, help="Website URL to extract categories from")
@click.option("--retailer-id", required=True, type=int, help="Retailer ID in the database")
@click.option("--headless/--no-headless", default=True, help="Run browser in headless mode")
@click.option("--force-refresh", is_flag=True, help="Force reload of initial page")
@click.option("--blueprint-only", "--dry-run", is_flag=True, help="Generate blueprint/template only (don't save to database)")
@click.option("--blueprint", type=click.Path(path_type=str), help="Existing blueprint path to run without LLM")
def extract_command(
    url: str,
    retailer_id: int,
    headless: bool,
    force_refresh: bool,
    blueprint_only: bool,
    blueprint: Optional[str],
) -> None:
    """Run the extraction workflow for a retailer.
    
    Use --blueprint-only to generate the template without saving categories to database.
    This is useful when you just want the extraction strategy for your scraper.
    """
    try:
        asyncio.run(
            _run_extract(
                url=url,
                retailer_id=retailer_id,
                headless=headless,
                force_refresh=force_refresh,
                blueprint_only=blueprint_only,
                blueprint_path=blueprint,
            )
        )
    except KeyboardInterrupt:
        console.print("\n[red]Cancelled by user[/red]")
        sys.exit(130)
    except ExtractorError as exc:
        console.print(Panel.fit(str(exc), title="Extraction Failed", border_style="red"))
        sys.exit(1)
    except Exception as exc:  # noqa: BLE001
        console.print(Panel.fit(str(exc), title="Unexpected Error", border_style="red"))
        sys.exit(1)


async def _run_extract(
    url: str,
    retailer_id: int,
    headless: bool,
    force_refresh: bool,
    blueprint_only: bool,
    blueprint_path: Optional[str],
) -> None:
    agent = CategoryExtractionAgent(retailer_id=retailer_id, site_url=url, headless=headless)
    
    try:
        console.print(
            Panel.fit(
                f"Retailer [bold]{retailer_id}[/bold]\nURL: [cyan]{url}[/cyan]",
                title="AI Category Extractor",
                border_style="blue",
            )
        )

        with Progress(SpinnerColumn(), TextColumn("{task.description}"), transient=True, console=console) as progress:
            stage = progress.add_task("Initialising...", start=True)

            await agent.initialize_browser()
            if blueprint_path:
                progress.update(stage, description="Loading blueprint...")
                blueprint = load_blueprint(blueprint_path)
                await agent.initialize_browser()
                analysis = blueprint.model_dump()
                agent.state["analysis"] = analysis
                progress.update(stage, description="Executing blueprint...")
                categories = await execute_blueprint(agent.page, blueprint, url)
            else:
                progress.update(stage, description="Analyzing navigation...")
                analysis = await agent.page_analyzer.analyze(url, force_refresh)
                console.print(f"[yellow]DEBUG: Analysis result: {analysis}[/yellow]")

                progress.update(stage, description="Extracting categories...")
                extraction = await agent.category_extractor.extract(url)
                console.print(f"[yellow]DEBUG: Extraction result: {extraction}[/yellow]")
                categories = extraction["categories"]
                console.print(f"[yellow]DEBUG: Categories count: {len(categories)}[/yellow]")

            if blueprint_only:
                progress.update(stage, description="Generating blueprint (no DB save)...")
                blueprint_file = await agent.blueprint_generator.generate(categories, analysis)
                console.print(_success_panel(len(categories), blueprint_file, saved=False))
            else:
                progress.update(stage, description="Saving categories...")
                save_stats = await agent.db.save_categories(categories, retailer_id=retailer_id)

                progress.update(stage, description="Generating blueprint...")
                blueprint_file = await agent.blueprint_generator.generate(categories, analysis)
                console.print(_success_panel(len(categories), blueprint_file, saved=True, save_stats=save_stats))
    finally:
        await agent.cleanup()


def _success_panel(total: int, blueprint_path: str, saved: bool, save_stats: Optional[dict] = None) -> Panel:
    lines = [
        f"Categories discovered: [green]{total}[/green]",
        f"Blueprint saved to: [cyan]{blueprint_path}[/cyan]",
    ]
    if saved and save_stats:
        lines.insert(1, f"Database -> saved: {save_stats.get('saved', 0)}, updated: {save_stats.get('updated', 0)}")
    return Panel("\n".join(lines), title="Extraction Complete", border_style="green")


def main() -> None:
    """Entry point for package execution."""
    cli()


if __name__ == "__main__":
    main()
