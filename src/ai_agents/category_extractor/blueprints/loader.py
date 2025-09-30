"""Blueprint loading utilities."""
from __future__ import annotations

import json
from pathlib import Path

from pydantic import ValidationError

from ..errors import BlueprintError
from ..tools.blueprint_generator import BlueprintModel


def load_blueprint(path: str | Path) -> BlueprintModel:
    file_path = Path(path)
    if not file_path.exists():
        raise BlueprintError(f"Blueprint not found: {file_path}")

    try:
        payload = json.loads(file_path.read_text(encoding="utf-8"))
        blueprint = BlueprintModel.model_validate(payload)
    except (OSError, json.JSONDecodeError) as exc:
        raise BlueprintError(f"Failed to read blueprint {path}: {exc}") from exc
    except ValidationError as exc:
        raise BlueprintError(f"Blueprint validation error: {exc}") from exc

    if blueprint.version != "1.0":
        raise BlueprintError(f"Unsupported blueprint version: {blueprint.version}")

    return blueprint


__all__ = ["load_blueprint"]
