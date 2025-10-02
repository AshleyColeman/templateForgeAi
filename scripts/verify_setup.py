"""Verify environment setup for the AI Category Extractor project."""
from __future__ import annotations

import importlib
import sys
from pathlib import Path
from typing import Iterable


REQUIRED_PACKAGES = {
    "strands-agents": "strands",
    "ollama": "ollama",
    "playwright": "playwright.async_api",
    "asyncpg": "asyncpg",
    "pydantic": "pydantic",
    "click": "click",
    "rich": "rich",
    "loguru": "loguru",
    "openai": "openai",
    "anthropic": "anthropic",
    "httpx": "httpx",
    "tenacity": "tenacity",
    "beautifulsoup4": "bs4",
}

DIRECTORIES = [
    "src/ai_agents/category_extractor",
    "src/ai_agents/category_extractor/tools",
    "src/ai_agents/category_extractor/utils",
    "src/ai_agents/category_extractor/blueprints",
    "tests/test_category_extractor",
    "logs",
]


def verify_python_version() -> bool:
    version = sys.version_info
    ok = version.major == 3 and version.minor >= 11
    message = f"Python version: {version.major}.{version.minor}.{version.micro}"
    print(f"{'✅' if ok else '❌'} {message}")
    return ok


def verify_imports() -> bool:
    all_ok = True
    for name, module in REQUIRED_PACKAGES.items():
        try:
            importlib.import_module(module)
            print(f"✅ {name} installed")
        except ImportError as exc:  # pragma: no cover - runtime check
            print(f"❌ {name} NOT installed: {exc}")
            all_ok = False
    return all_ok


def verify_directories() -> bool:
    all_ok = True
    for directory in DIRECTORIES:
        if Path(directory).exists():
            print(f"✅ Directory exists: {directory}")
        else:
            print(f"❌ Directory missing: {directory}")
            all_ok = False
    return all_ok


def verify_env_file() -> bool:
    env_file = Path(".env")
    if env_file.exists():
        print("✅ .env file exists")
        return True
    print("⚠️  .env file missing (copy from .env.example)")
    return False


def run_checks(checks: Iterable[callable]) -> bool:
    print("\n🔍 Verifying Environment Setup\n")
    results = [check() for check in checks]
    print("\n" + "=" * 50)
    if all(results):
        print("✅ All checks passed! Environment is ready.")
        return True
    print("❌ Some checks failed. Please fix the issues above.")
    return False


if __name__ == "__main__":
    SUCCESS = run_checks(
        [
            verify_python_version,
            verify_imports,
            verify_directories,
            verify_env_file,
        ]
    )
    sys.exit(0 if SUCCESS else 1)
