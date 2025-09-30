"""Centralised Loguru configuration."""
from __future__ import annotations

import sys
from typing import Optional

from loguru import logger

from ..config import get_config

_LOG_INITIALIZED = False


def setup_logger() -> None:
    """Configure loguru sinks based on configuration."""
    global _LOG_INITIALIZED
    if _LOG_INITIALIZED:
        return

    config = get_config()

    logger.remove()
    logger.add(
        sys.stdout,
        level=config.log_level,
        colorize=True,
        format=(
            "<green>{time:YYYY-MM-DD HH:mm:ss}</green> | "
            "<level>{level: <8}</level> | retailer={extra[retailer_id]} | "
            "<cyan>{name}</cyan>:<cyan>{function}</cyan> - <level>{message}</level>"
        ),
        enqueue=True,
    )

    if config.log_file:
        logger.add(
            config.log_file,
            level=config.log_level,
            rotation=config.log_rotation,
            retention=config.log_retention,
            encoding="utf-8",
            enqueue=True,
        )

    _LOG_INITIALIZED = True


def get_logger(retailer_id: Optional[int] = None):
    """Return logger bound with retailer context."""
    setup_logger()
    return logger.bind(retailer_id=retailer_id or "n/a")


log = get_logger()

__all__ = ["setup_logger", "get_logger", "log"]
