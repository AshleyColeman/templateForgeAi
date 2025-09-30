"""Custom exception classes for AI category extractor."""
from __future__ import annotations


class ExtractorError(Exception):
    """Base exception for extractor errors."""


class NavigationError(ExtractorError):
    """Raised when page navigation fails."""


class AnalysisError(ExtractorError):
    """Raised when LLM-driven analysis fails."""


class ExtractionError(ExtractorError):
    """Raised when category harvesting fails."""


class DatabaseError(ExtractorError):
    """Raised during database operations."""


class BotDetectionError(ExtractorError):
    """Raised when the retailer blocks automation or shows CAPTCHA."""


class ValidationError(ExtractorError):
    """Raised when data validation fails."""


class BlueprintError(ExtractorError):
    """Raised when blueprint generation or execution fails."""


__all__ = [
    "ExtractorError",
    "NavigationError",
    "AnalysisError",
    "ExtractionError",
    "DatabaseError",
    "BotDetectionError",
    "ValidationError",
    "BlueprintError",
]
