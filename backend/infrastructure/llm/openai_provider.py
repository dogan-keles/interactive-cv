"""
OpenAI LLM provider - replaces Groq provider.
"""

from abc import ABC, abstractmethod
from typing import Optional
import os
import logging

try:
    from openai import AsyncOpenAI
except ImportError:
    AsyncOpenAI = None

logger = logging.getLogger(__name__)


class BaseLLMProvider(ABC):
    """Abstract LLM provider interface."""
    
    @abstractmethod
    async def generate(
        self,
        prompt: str,
        temperature: Optional[float] = None,
        max_tokens: Optional[int] = None,
        system_prompt: Optional[str] = None,
    ) -> str:
        pass


class OpenAIProvider(BaseLLMProvider):
    """OpenAI LLM provider using GPT-4o-mini."""
    
    def __init__(
        self,
        api_key: Optional[str] = None,
        model: str = "gpt-4o-mini",
        default_temperature: float = 0.3,
        default_max_tokens: int = 1024,
    ):
        if AsyncOpenAI is None:
            raise ImportError("openai package required. Install: pip install openai")
        
        self.api_key = api_key or os.getenv("OPENAI_API_KEY")
        if not self.api_key:
            raise ValueError("OPENAI_API_KEY missing. Check your .env file.")
        
        self.client = AsyncOpenAI(api_key=self.api_key)
        self.model_name = model
        self.default_temperature = default_temperature
        self.default_max_tokens = default_max_tokens
    
    async def generate(
        self,
        prompt: str,
        temperature: Optional[float] = None,
        max_tokens: Optional[int] = None,
        system_prompt: Optional[str] = None,
    ) -> str:
        """Generate text using OpenAI API."""
        try:
            messages = []
            if system_prompt:
                messages.append({"role": "system", "content": system_prompt})
            messages.append({"role": "user", "content": prompt})
            
            response = await self.client.chat.completions.create(
                model=self.model_name,
                messages=messages,
                temperature=temperature if temperature is not None else self.default_temperature,
                max_tokens=max_tokens if max_tokens is not None else self.default_max_tokens,
            )
            
            content = response.choices[0].message.content
            
            if not content:
                logger.warning("Empty response from OpenAI API")
                return "I couldn't generate a response at this time."
            
            return content.strip()
        
        except Exception as e:
            logger.error(f"OpenAI API error: {e}")
            return f"Technical error occurred (OpenAI). Details: {str(e)}"