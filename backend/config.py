"""
Configuration for AI Lab Dashboard.

Loads environment variables from .env via python-dotenv.
All provider keys are optional; missing keys default to None and simply
disable that provider at runtime — the server will not crash on startup.
"""
from __future__ import annotations

import os
from pathlib import Path

from dotenv import load_dotenv

# Load .env from the project root (one level above this file).
_env_path = Path(__file__).resolve().parent.parent / ".env"
load_dotenv(dotenv_path=_env_path, override=False)


class Settings:
    """Central settings object.  All attributes are read once at import time."""

    # OpenAI
    openai_api_key: str | None = os.getenv("OPENAI_API_KEY") or None

    # Anthropic
    anthropic_api_key: str | None = os.getenv("ANTHROPIC_API_KEY") or None

    # Google Gemini
    gemini_api_key: str | None = os.getenv("GEMINI_API_KEY") or None

    # OpenRouter
    openrouter_api_key: str | None = os.getenv("OPENROUTER_API_KEY") or None
    openrouter_management_key: str | None = (
        os.getenv("OPENROUTER_MANAGEMENT_KEY") or None
    )

    # Tavily
    tavily_api_key: str | None = os.getenv("TAVILY_API_KEY") or None

    # Local inference (no key required)
    ollama_base_url: str | None = os.getenv("OLLAMA_BASE_URL") or None
    lmstudio_base_url: str | None = os.getenv("LMSTUDIO_BASE_URL") or None


settings = Settings()
