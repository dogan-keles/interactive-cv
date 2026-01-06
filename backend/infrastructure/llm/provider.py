from abc import ABC, abstractmethod
from typing import Optional
import os
import logging

# Groq kütüphanesini kullanıyoruz
try:
    from groq import AsyncGroq
except ImportError:
    AsyncGroq = None

logger = logging.getLogger(__name__)

class BaseLLMProvider(ABC):
    @abstractmethod
    async def generate(
        self,
        prompt: str,
        temperature: Optional[float] = None,
        max_tokens: Optional[int] = None,
    ) -> str:
        pass

class GroqProvider(BaseLLMProvider):
    """
    Groq LLM provider (Using Llama-3 models).
    Get API key from: https://console.groq.com/
    """
    
    def __init__(
        self,
        api_key: Optional[str] = None,
        model: str = "llama-3.3-70b-versatile",
        default_temperature: float = 0.7,
        default_max_tokens: int = 1024,
    ):
        if AsyncGroq is None:
            raise ImportError("groq paketi gerekli. Kurmak için: pip install groq")
        
        # API Key'i GROQ_API_KEY olarak çevreden alıyoruz
        self.api_key = api_key or os.getenv("GROQ_API_KEY")
        if not self.api_key:
            raise ValueError("GROQ_API_KEY eksik! Lütfen .env dosyanı kontrol et.")
        
        # Groq client başlatılıyor
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
        try:
            # Groq API çağrısı
            response = await self.client.chat.completions.create(
                model=self.model_name,
                messages=[
                    {"role": "system", "content": "Sen yardımcı bir asistan ve profesyonel bir CV uzmanısın."},
                    {"role": "user", "content": prompt}
                ],
                temperature=temperature if temperature is not None else self.default_temperature,
                max_tokens=max_tokens if max_tokens is not None else self.default_max_tokens,
            )
            
            content = response.choices[0].message.content
            
            if not content:
                logger.warning("Groq API'den boş yanıt döndü.")
                return "Üzgünüm, şu an bir yanıt oluşturamadım."
            
            return content.strip()
        
        except Exception as e:
            logger.error(f"Groq API Hatası: {e}")
            # Hata durumunda kullanıcıya anlamlı bir mesaj dönüyoruz
            return f"Şu an teknik bir sorun yaşıyorum (Groq Error). Detay: {str(e)}"