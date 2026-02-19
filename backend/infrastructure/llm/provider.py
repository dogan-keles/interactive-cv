"""
LLM provider abstraction.
"""

from abc import ABC, abstractmethod
from typing import Optional
import os
import logging

try:
    from groq import AsyncGroq
except ImportError:
    AsyncGroq = None

logger = logging.getLogger(__name__)


class BaseLLMProvider(ABC):
    """Abstract LLM provider interface."""
    
    @abstractmethod
    async def generate(
        self,
        prompt: str,
        temperature: Optional[float] = None,
        max_tokens: Optional[int] = None,
    ) -> str:
        pass


class GroqProvider(BaseLLMProvider):
    """Groq LLM provider using Llama models."""
    
    def __init__(
        self,
        api_key: Optional[str] = None,
        model: str = "llama-3.3-70b-versatile",
        default_temperature: float = 0.7,
        default_max_tokens: int = 1024,
    ):
        if AsyncGroq is None:
            raise ImportError("groq package required. Install: pip install groq")
        
        self.api_key = api_key or os.getenv("GROQ_API_KEY")
        if not self.api_key:
            raise ValueError("GROQ_API_KEY missing. Check your .env file.")
        
        self.client = AsyncGroq(api_key=self.api_key)
        self.model_name = model
        self.default_temperature = default_temperature
        self.default_max_tokens = default_max_tokens
    
    async def generate(
        self,
        prompt: str,
        temperature: Optional[float] = None,
        max_tokens: Optional[int] = None,
    ) -> str:
        """Generate text using Groq API."""
        try:
            response = await self.client.chat.completions.create(
                model=self.model_name,
                messages=[
                    {"role": "system", "content": "You are a helpful assistant and professional CV expert."},
                    {"role": "user", "content": prompt}
                ],
                temperature=temperature if temperature is not None else self.default_temperature,
                max_tokens=max_tokens if max_tokens is not None else self.default_max_tokens,
            )
            
            content = response.choices[0].message.content
            
            if not content:
                logger.warning("Empty response from Groq API")
                return "I couldn't generate a response at this time."
            
            return content.strip()
        
        except Exception as e:
            logger.error(f"Groq API error: {e}")
            return f"Technical error occurred (Groq). Details: {str(e)}"