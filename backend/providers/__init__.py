"""
Provider registry.

Maps each provider's lowercase ``name`` to its concrete instance.  Routers use
this single registry so a newly added provider is picked up everywhere without
touching routing or frontend logic.
"""
from __future__ import annotations

from . import anthropic, gemini, lmstudio, ollama, openai, openrouter, tavily
from .base import BaseProvider

PROVIDERS: dict[str, BaseProvider] = {
    openai.provider.name: openai.provider,
    anthropic.provider.name: anthropic.provider,
    gemini.provider.name: gemini.provider,
    openrouter.provider.name: openrouter.provider,
    tavily.provider.name: tavily.provider,
    ollama.provider.name: ollama.provider,
    lmstudio.provider.name: lmstudio.provider,
}

__all__ = ["PROVIDERS"]