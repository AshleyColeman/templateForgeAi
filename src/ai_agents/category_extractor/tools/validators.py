"""Validation helpers for category data."""
from __future__ import annotations

from typing import Dict, Iterable, List, Optional

from ..errors import ValidationError


def validate_category(category: Dict[str, object]) -> bool:
    if not category.get("name"):
        raise ValidationError("Category name is required")
    if not category.get("url"):
        raise ValidationError("Category URL is required")
    return True


def validate_hierarchy(categories: Iterable[Dict[str, object]]) -> bool:
    id_set = {category.get("id") for category in categories}
    for category in categories:
        parent_id: Optional[object] = category.get("parent_id")
        if parent_id is not None and parent_id not in id_set:
            raise ValidationError("Parent id missing for category hierarchy")
    return True


__all__ = ["validate_category", "validate_hierarchy"]
