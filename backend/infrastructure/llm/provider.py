"""
Legacy import - redirects to openai_provider.
"""
from backend.infrastructure.llm.openai_provider import BaseLLMProvider, OpenAIProvider

__all__ = ["BaseLLMProvider", "OpenAIProvider"]
