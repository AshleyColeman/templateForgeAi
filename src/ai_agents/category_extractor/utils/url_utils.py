"""URL utility helpers (to be implemented in later tasks)."""
from __future__ import annotations

from urllib.parse import urljoin, urlparse, urlunparse


def ensure_absolute(url: str, base_url: str) -> str:
    """Return absolute URL given potential relative path."""
    return urljoin(base_url, url)


def normalize_url(url: str) -> str:
    """Normalize URL by removing fragments and redundant slashes."""
    parsed = urlparse(url)
    normalized = parsed._replace(fragment="")
    return urlunparse(normalized)


__all__ = ["ensure_absolute", "normalize_url"]
