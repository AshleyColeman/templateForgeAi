"""Tool that generates reusable extraction blueprints."""
from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field

from ..config import get_config
from ..errors import BlueprintError
from ..utils.logger import get_logger


class BlueprintMetadata(BaseModel):
    site_url: str
    retailer_id: int
    retailer_name: Optional[str] = None
    generated_at: str = Field(default_factory=lambda: datetime.utcnow().isoformat())
    generated_by: str = "ai_category_extractor"
    agent_version: str = "0.1.0"
    confidence_score: float


class BlueprintModel(BaseModel):
    version: str = "1.0"
    metadata: BlueprintMetadata
    extraction_strategy: Dict[str, Any]
    selectors: Dict[str, Any]
    interactions: List[Dict[str, Any]]
    validation_rules: Dict[str, Any]
    extraction_stats: Dict[str, Any]
    edge_cases: List[Dict[str, Any]] = Field(default_factory=list)
    notes: List[str] = Field(default_factory=list)


class BlueprintGeneratorTool:
    """Generate JSON blueprints after successful extraction."""

    def __init__(self, agent: "CategoryExtractionAgent") -> None:
        self.agent = agent
        self.config = get_config()
        self.logger = get_logger(agent.retailer_id)

    async def generate(self, categories: List[Dict[str, Any]], strategy: Dict[str, Any]) -> str:
        if not categories:
            raise BlueprintError("Cannot generate blueprint with zero categories")
        if not strategy:
            raise BlueprintError("Strategy data missing. Ensure PageAnalyzer ran successfully")

        retailer = await self.agent.db.get_retailer_info(self.agent.retailer_id)
        metadata = BlueprintMetadata(
            site_url=self.agent.site_url,
            retailer_id=self.agent.retailer_id,
            retailer_name=retailer.get("name") if retailer else None,
            confidence_score=strategy.get("confidence", 0.5),
        )

        blueprint = BlueprintModel(
            metadata=metadata,
            extraction_strategy=self._build_strategy_section(strategy),
            selectors=strategy.get("selectors", {}),
            interactions=strategy.get("interactions", []),
            validation_rules=self._build_validation_rules(categories, strategy),
            extraction_stats=self._build_stats(categories),
            notes=strategy.get("notes", []),
        )

        path = self._write_blueprint(blueprint)
        self.agent.state["blueprint_path"] = str(path)
        return str(path)

    def _build_strategy_section(self, strategy: Dict[str, Any]) -> Dict[str, Any]:
        return {
            "navigation_type": strategy.get("navigation_type", "unknown"),
            "complexity": strategy.get("complexity", "unknown"),
            "requires_javascript": strategy.get("requires_javascript", True),
            "dynamic_loading": strategy.get("dynamic_loading", {}),
        }

    def _build_validation_rules(self, categories: List[Dict[str, Any]], strategy: Dict[str, Any]) -> Dict[str, Any]:
        total = len(categories)
        max_depth = max((category.get("depth", 0) for category in categories), default=0)
        return {
            "min_categories": max(1, total // 4),
            "max_categories": total * 2,
            "max_depth": max_depth,
            "required_fields": ["name", "url"],
            "url_pattern": strategy.get("url_pattern", ""),
        }

    def _build_stats(self, categories: List[Dict[str, Any]]) -> Dict[str, Any]:
        depth_counts: Dict[int, int] = {}
        for category in categories:
            depth = int(category.get("depth", 0))
            depth_counts[depth] = depth_counts.get(depth, 0) + 1
        return {
            "total_categories": len(categories),
            "max_depth": max(depth_counts.keys(), default=0),
            "categories_by_depth": {str(depth): count for depth, count in depth_counts.items()},
        }

    def _write_blueprint(self, blueprint: BlueprintModel) -> Path:
        output_dir = Path(self.config.blueprint_dir)
        output_dir.mkdir(parents=True, exist_ok=True)
        filename = f"retailer_{self.agent.retailer_id}_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}.json"
        path = output_dir / filename
        try:
            with path.open("w", encoding="utf-8") as handle:
                json.dump(blueprint.model_dump(mode="json"), handle, indent=2)
        except OSError as exc:
            raise BlueprintError(f"Failed to write blueprint to {path}: {exc}") from exc
        self.logger.info("Blueprint saved to {}", path)
        return path


__all__ = ["BlueprintGeneratorTool", "BlueprintModel", "BlueprintMetadata"]
