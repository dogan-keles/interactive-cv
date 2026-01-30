"""
CV Agent implementation - FIXED VERSION

Handles CV download requests and CV-related queries.

CHANGES:
- Uses session factory instead of global session (thread-safe)
- Creates and closes sessions properly for each request
"""

import os
import logging
from typing import Optional, Callable

from sqlalchemy.orm import Session

from backend.infrastructure.llm.provider import BaseLLMProvider
from backend.orchestrator.types import RequestContext

logger = logging.getLogger(__name__)


class CVAgent:
    """
    Agent for handling CV download and CV-related queries.
    """

    def __init__(
        self,
        llm_provider: BaseLLMProvider,
        db_session_factory: Optional[Callable[[], Session]] = None,
    ):
        """
        Initialize CV Agent.
        
        Args:
            llm_provider: LLM provider for generating responses
            db_session_factory: Factory function to create database sessions (optional)
        """
        self.llm_provider = llm_provider
        self.db_session_factory = db_session_factory

    async def process(self, context: RequestContext) -> str:
        """
        Process CV-related query.
        
        Args:
            context: Request context with user query
            
        Returns:
            Response with CV download link
        """
        # Get frontend URL from environment variable
        frontend_url = os.getenv("FRONTEND_URL", "https://dogankeles.com")
        download_url = f"{frontend_url}/download-cv"
        
        # Build prompt for LLM
        prompt = self._build_prompt(context, download_url)
        
        # Generate response using LLM
        response = await self.llm_provider.generate(
            prompt=prompt,
            temperature=0.7,
            max_tokens=500,
        )
        
        return response.strip()

    def _build_prompt(
        self,
        context: RequestContext,
        download_url: str,
    ) -> str:
        """
        Build prompt for LLM with CV download information.
        
        Args:
            context: Request context
            download_url: URL to download page
            
        Returns:
            Formatted prompt string
        """
        prompt = f"""You are a professional CV assistant helping someone download Doğan Keleş's CV.

USER QUERY: {context.user_query}
LANGUAGE: Respond in {context.language.value}

INFORMATION ABOUT DOĞAN KELEŞ:
- Position: Backend Engineer & AI Specialist
- Specialization: Python, FastAPI, AI Integration, Machine Learning
- Location: Mardin, Turkey
- LinkedIn: https://linkedin.com/in/dogan-keles
- GitHub: https://github.com/dogan-keles

CV INCLUDES:
- Technical skills and expertise (19+ technologies)
- Work experience and professional projects
- GitHub portfolio with multiple projects
- Education background and certifications
- Contact information

CV DOWNLOAD LINK: {download_url}

INSTRUCTIONS:
1. Respond professionally and warmly in {context.language.value}
2. Confirm you're happy to share the CV
3. Briefly mention what the CV includes (1-2 sentences)
4. Provide the download link clearly
5. Explain that they need to enter their email to download
6. Keep response concise and friendly (3-5 sentences max)
7. DO NOT make up information - only use what's provided above

Generate a helpful response about downloading the CV.
"""
        
        return prompt