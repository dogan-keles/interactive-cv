import logging
from typing import Optional
from infrastructure.llm.provider import BaseLLMProvider
from orchestrator.types import RequestContext

logger = logging.getLogger(__name__)

class CVAgent:
    """
    CV ile ilgili soruları işleyen ve yanıtlayan ajan.
    """
    
    def __init__(self, llm_provider: BaseLLMProvider, db_session: Optional[any] = None):
        # db_session=None varsayılan değeri main.py'deki hatayı engeller
        self.llm_provider = llm_provider
        self.db_session = db_session
    
    async def process(self, context: RequestContext) -> str:
        """
        Kullanıcının CV hakkındaki sorusunu LLM kullanarak yanıtlar.
        """
        prompt = f"""
        Sen bir CV uzmanısın. Kullanıcının sorusuna profesyonel bir dille yanıt ver.
        
        Kullanıcı Sorusu: {context.query}
        Dil: {context.language.value}
        
        Not: Şu an veritabanı bağlantısı kapalıdır, genel bir profesyonel yanıt oluştur.
        """
        
        try:
       
            response = await self.llm_provider.generate(prompt)
            return response
        except Exception as e:
            logger.error(f"CVAgent error: {e}")
            if context.language.value == "tr":
                return "CV bilgilerine şu an ulaşılamıyor, lütfen teknik ekiple iletişime geçin."
            return "CV information is currently unavailable, please contact technical support."