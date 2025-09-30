# Task 9: Error Handling & Logging

**Status**: 🔒 Blocked (depends on Tasks 1-8)  
**Estimated Time**: 4-5 hours  
**Dependencies**: All prior implementation tasks (1-8)  
**Priority**: High (production hardening)

---

## 📋 Objective

Implement consistent error handling, retry logic, and structured logging across the project. This includes extending the custom exception hierarchy, centralizing Loguru configuration, adding contextual logging, and ensuring retries/backoffs exist for flaky operations (network/browser/database).

## 🎯 Success Criteria

- [ ] `errors.py` updated with domain-specific exceptions (already scaffolded in Task 3) and documented usage
- [ ] `utils/logger.py` configures Loguru sinks per config (console + optional file) with rotation/retention
- [ ] Retry decorators (Tenacity) applied to Bedrock and Playwright navigation hotspots
- [ ] Helper `capture_exception` method logs error + attaches to agent state
- [ ] Structured log fields include retailer_id, url, stage where applicable
- [ ] Global logging level respects `.env` `LOG_LEVEL`
- [ ] Error handling guidelines documented for developers

## 📝 Specifications

### File: `src/ai_agents/category_extractor/errors.py`

Ensure the file includes the following structure (extend if missing):

```python
"""Custom exception classes for AI category extractor."""

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
```

Add docstrings describing when to raise each exception and update imports across modules accordingly.

### File: `src/ai_agents/category_extractor/utils/logger.py`

```python
"""Centralized Loguru configuration."""
from __future__ import annotations

import os
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
        sink=lambda msg: print(msg, end=""),
        level=config.log_level,
        colorize=True,
        format="<green>{time:YYYY-MM-DD HH:mm:ss}</green> | "
               "<level>{level: <8}</level> | "
               "retailer={extra[retailer_id]!s} | "
               "<cyan>{name}</cyan>:<cyan>{function}</cyan> - <level>{message}</level>",
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
    setup_logger()
    return logger.bind(retailer_id=retailer_id or "n/a")
```

Update modules to call `get_logger(reailer_id)` instead of importing `log` directly, or keep a module-level logger as appropriate (ensure retailer context is included where possible).

### Retry Decorators

- Apply `tenacity.retry` to:
  - Bedrock API calls (`PageAnalyzerTool._call_bedrock`)
  - Database persistence helper (if transient errors occur)
  - Playwright navigation functions (`CategoryExtractorTool._navigate` or dedicated helper)

Use exponential backoff (`wait_fixed` or `wait_exponential`) and limited attempts defined by config (`MAX_RETRIES`, `RETRY_DELAY`).

### Error Capturing

Add helper method on the agent (or utility) to capture errors:

```python
async def capture_error(agent, exc: Exception, stage: str) -> None:
    message = f"{stage} failed: {exc}"
    agent.state.setdefault("errors", []).append(message)
    log.error(message)
```

Ensure each tool calls this helper before raising upward so the CLI can display aggregated issues.

### Documentation

Add an "Error Handling" section to `src/ai_agents/category_extractor/README.md` summarizing:
- Common exception classes and meanings
- Logging configuration and how to adjust via `.env`
- Tips for interpreting logs (retailer_id binding, blueprint path, etc.)

## 🔧 Implementation Steps

1. **Finalize exception hierarchy**: ensure all modules raise meaningful exceptions (no bare `Exception`).
2. **Centralize logging**: configure Loguru once via `setup_logger()`; adjust imports in agent/tools/cli to fetch bound logger.
3. **Add retries**: wrap network/browser operations with Tenacity decorators referencing config values.
4. **Track errors in agent state**: call helper whenever a recoverable error occurs.
5. **Update README** with new section (short paragraphs on using logs and debugging).
6. **Smoke test** by forcing errors (e.g., invalid URL) and confirming CLI output + log messages are clear.

## ✅ Validation Checklist

- [ ] `LOG_LEVEL=DEBUG` surfaces verbose logs from CLI run
- [ ] Error logs include retailer context and stage information
- [ ] Retries confirmed (e.g., intentionally fail first Bedrock call, ensure retry attempts logged)
- [ ] README updated with error-handling guidance
- [ ] MyPy + lint still pass after logger helper refactors

## 🧪 Manual Testing

```bash
LOG_LEVEL=DEBUG poetry run python -m src.ai_agents.category_extractor.cli extract \
    --url https://invalid.example \
    --retailer-id 1
# Expect graceful failure with logged NavigationError
```

## 📝 Deliverables

1. Updated `errors.py`, `utils/logger.py`, and other modules using new helpers
2. README error-handling section
3. Verification notes added to `MASTER_TASKLIST.md`

## 🚨 Common Issues & Solutions

| Issue | Symptom | Fix |
|-------|---------|-----|
| Duplicate logs | Messages appear twice | Ensure `setup_logger()` called only once (guard with `_LOG_INITIALIZED`) |
| Missing retailer context | Logs show `retailer=n/a` | Bind logger with retailer ID in agent/CLI context |
| Retry floods logs | Too many retry attempts | Tune `MAX_RETRIES` and delays in config; log only at INFO for attempts |
| Exceptions swallowed | Silent failures | Re-raise custom exceptions after logging; avoid bare `except` without `raise` |

## 📚 Next Steps

After Task 9:
1. Update `MASTER_TASKLIST.md` status/time.
2. Commit logging/error-handling enhancements.
3. Begin **Task 10: Blueprint Execution System** to leverage generated blueprints.

**Last Updated**: 2025-09-30
