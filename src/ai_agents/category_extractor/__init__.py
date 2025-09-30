"""
AI-powered category extraction for e-commerce websites.

This package provides an autonomous agent that can analyze website structure
and extract product categories without manual configuration.
"""

__version__ = "0.1.0"
__author__ = "Ashley Coleman"

try:
    from .agent import CategoryExtractionAgent  # noqa: F401
    from .database import CategoryDatabase  # noqa: F401
    from .config import get_config  # noqa: F401
except ImportError:  # pragma: no cover - modules not yet implemented
    # Modules will be available once corresponding tasks are complete.
    CategoryExtractionAgent = None  # type: ignore
    CategoryDatabase = None  # type: ignore
    get_config = None  # type: ignore

__all__ = [
    "CategoryExtractionAgent",
    "CategoryDatabase",
    "get_config",
]
