"""
CV Agent - Handles CV download requests and CV-related queries.
"""

import os
import logging
from typing import Optional, Callable

from sqlalchemy.orm import Session

from backend.infrastructure.llm.provider import BaseLLMProvider
from backend.orchestrator.types import RequestContext
from backend.tools import profile_tools

logger = logging.getLogger(__name__)


class CVAgent:
    """Agent for handling CV download and CV-related queries."""

    def __init__(
        self,
        llm_provider: BaseLLMProvider,
        db_session_factory: Optional[Callable[[], Session]] = None,
    ):
        self.llm_provider = llm_provider
        self.db_session_factory = db_session_factory

    async def process(self, context: RequestContext) -> str:
        """Process CV-related query."""
        if self.db_session_factory is None:
            return "CV data is not available. Database connection is required."

        db = self.db_session_factory()
        
        try:
            # Get profile basic info from database
            basic_info = await profile_tools.get_profile_basic_info(
                profile_id=context.profile_id,
                db_session=db,
            )
            
            # Get frontend URL from environment
            frontend_url = os.getenv("FRONTEND_URL", "http://localhost:3000")
            download_url = f"{frontend_url}/download-cv"
            
            # Build prompt with dynamic data
            prompt = self._build_prompt(context, download_url, basic_info)
            
            # Generate response
            response = await self.llm_provider.generate(
                prompt=prompt,
                temperature=0.7,
                max_tokens=500,
            )
            
            return response.strip()
        
        except Exception as e:
            logger.error(f"CVAgent error processing query: {e}", exc_info=True)
            raise
        
        finally:
            db.close()

    def _build_prompt(
        self,
        context: RequestContext,
        download_url: str,
        basic_info: dict,
    ) -> str:
        """Build prompt with CV download information."""
        # Extract info from basic_info
        name = basic_info.get("name", "the candidate")
        location = basic_info.get("location", "Turkey")
        linkedin_url = basic_info.get("linkedin_url", "")
        github_username = basic_info.get("github_username", "")
        github_url = f"https://github.com/{github_username}" if github_username else ""
        
        prompt = f"""You are a professional CV assistant helping someone download {name}'s CV.

USER QUERY: {context.user_query}
LANGUAGE: Respond in {context.language.value}

CANDIDATE INFORMATION:
- Name: {name}
- Location: {location}"""
        
        if linkedin_url:
            prompt += f"\n- LinkedIn: {linkedin_url}"
        
        if github_url:
            prompt += f"\n- GitHub: {github_url}"
        
        prompt += f"""

CV INCLUDES:
- Technical skills and expertise
- Work experience and professional projects
- GitHub portfolio with projects
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