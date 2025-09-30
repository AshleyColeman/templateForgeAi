"""Tests for logger configuration helpers."""
from __future__ import annotations

from src.ai_agents.category_extractor.utils.logger import get_logger, setup_logger


def test_get_logger_binds_retailer() -> None:
    setup_logger()
    logger = get_logger(42)
    bound_msg = []

    def sink(message):
        bound_msg.append(message)

    # Temporarily add sink to capture output
    handler_id = logger.add(sink)
    logger.info("hello")
    logger.remove(handler_id)

    assert bound_msg, "Logger sink should capture output"
    assert "retailer=42" in bound_msg[0]
