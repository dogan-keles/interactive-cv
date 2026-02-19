"""
Profile Agent - Handles questions about professional skills, experience, and background.
"""

import logging
import re
from typing import Optional, Callable

from sqlalchemy.orm import Session

from backend.infrastructure.llm.provider import BaseLLMProvider
from backend.orchestrator.types import RequestContext
from backend.data_access.vector_db.retrieval import RAGRetrievalPipeline
from backend.agents.prompts import (
    PROFILE_AGENT_SYSTEM_PROMPT,
    PROFILE_AGENT_INSTRUCTIONS,
)
from backend.tools import profile_tools

logger = logging.getLogger(__name__)


class ProfileAgent:
    """Agent for handling profile-related queries."""
    
    def __init__(
        self,
        llm_provider: BaseLLMProvider,
        db_session_factory: Optional[Callable[[], Session]] = None,
        retrieval_pipeline: Optional[RAGRetrievalPipeline] = None,
    ):
        self.llm_provider = llm_provider
        self.db_session_factory = db_session_factory
        self.retrieval_pipeline = retrieval_pipeline
    
    async def process(self, context: RequestContext) -> str:
        """Process profile-related query."""
        try:
            profile_data = await self._gather_profile_data(context)
            rag_context = await self._get_rag_context(context)
            prompt = self._build_prompt(context, profile_data, rag_context)
            
            response = await self.llm_provider.generate(
                prompt=prompt,
                temperature=0.7,
                max_tokens=1000,
            )
            
            return self._clean_response(response.strip())
        
        except Exception as e:
            logger.error(f"ProfileAgent error: {e}", exc_info=True)
            raise
    
    def _clean_response(self, response: str) -> str:
        """Remove proficiency mentions and clean spacing."""
        proficiency_patterns = [
            r'\bproficiency in\b',
            r'\bproficient in\b',
        ]
        
        cleaned = response
        for pattern in proficiency_patterns:
            cleaned = re.sub(pattern, '', cleaned, flags=re.IGNORECASE)
        
        return re.sub(r'\s+', ' ', cleaned).strip()
    
    async def _gather_profile_data(self, context: RequestContext) -> dict:
        """Gather relevant profile data using tools."""
        if not self.db_session_factory:
            logger.warning("No database session factory available")
            return {}
        
        db = self.db_session_factory()
        
        try:
            query_lower = context.user_query.lower()
            data = {}
            
            contact_keywords = [
                "contact", "email", "reach", "iletişim", "e-posta", "ulaş", "peywendî"
            ]
            if any(k in query_lower for k in contact_keywords):
                data["basic_info"] = await profile_tools.get_profile_basic_info(
                    context.profile_id, db
                )
            
            skill_keywords = [
                "skill", "yetenek", "teknoloji", "technology", "expertise", 
                "uzmanlık", "know", "biliyor", "can", "dizane", "jêhatî"
            ]
            if any(k in query_lower for k in skill_keywords):
                data["skills"] = await profile_tools.get_profile_skills(
                    context.profile_id, db
                )
            
            experience_keywords = [
                "experience", "deneyim", "work", "iş", "career", "kariyer", 
                "job", "pozisyon", "company", "şirket", "worked", "kar", "ezmûn"
            ]
            if any(k in query_lower for k in experience_keywords):
                data["experiences"] = await profile_tools.get_profile_experiences(
                    context.profile_id, db
                )
            
            project_keywords = [
                "project", "proje", "portfolio", "built", "created", 
                "developed", "çalışma"
            ]
            if any(k in query_lower for k in project_keywords):
                data["projects"] = await profile_tools.get_profile_projects(
                    context.profile_id, db
                )
            
            summary_keywords = [
                "summary", "özet", "background", "geçmiş", "about", 
                "hakkında", "who", "kim", "tell me", "yourself", "çi", "kî"
            ]
            if any(k in query_lower for k in summary_keywords):
                data["summary"] = await profile_tools.get_profile_summary(
                    context.profile_id, db
                )
            
            if not data:
                data["basic_info"] = await profile_tools.get_profile_basic_info(
                    context.profile_id, db
                )
                data["summary"] = await profile_tools.get_profile_summary(
                    context.profile_id, db
                )
                data["skills"] = await profile_tools.get_profile_skills(
                    context.profile_id, db
                )
            
            return data
        
        finally:
            db.close()
    
    async def _get_rag_context(self, context: RequestContext) -> Optional[str]:
        """Get RAG context via semantic search if available."""
        if not self.retrieval_pipeline:
            return None
        
        if context.rag_context:
            return context.rag_context
        
        try:
            rag_context = await self.retrieval_pipeline.retrieve_context(
                query=context.user_query,
                profile_id=context.profile_id,
                top_k=3,
                min_score=0.3,
            )
            return rag_context if rag_context else None
        except Exception as e:
            logger.warning(f"RAG retrieval failed: {e}")
            return None
    
    def _build_prompt(
        self,
        context: RequestContext,
        profile_data: dict,
        rag_context: Optional[str],
    ) -> str:
        """Build complete prompt for LLM."""
        prompt_parts = [
            PROFILE_AGENT_SYSTEM_PROMPT,
            "",
            PROFILE_AGENT_INSTRUCTIONS,
            "",
            "=" * 80,
            "USER'S QUESTION:",
            f'"{context.user_query}"',
            "",
            "⚠️  RESPOND IN THE SAME LANGUAGE AS THE QUESTION ABOVE",
            "=" * 80,
            "",
        ]
        
        if profile_data:
            prompt_parts.append("PROFILE DATA:")
            prompt_parts.append("━" * 80)
            
            if "basic_info" in profile_data and profile_data["basic_info"]:
                info = profile_data["basic_info"]
                prompt_parts.append(f"Name: {info.get('name', 'N/A')}")
                if info.get('email'):
                    prompt_parts.append(f"Email: {info['email']}")
                if info.get('location'):
                    prompt_parts.append(f"Location: {info['location']}")
                if info.get('linkedin_url'):
                    prompt_parts.append(f"LinkedIn: {info['linkedin_url']}")
                if info.get('github_username'):
                    prompt_parts.append(f"GitHub: https://github.com/{info['github_username']}")
                prompt_parts.append("")
            
            if "summary" in profile_data and profile_data["summary"]:
                prompt_parts.append("SUMMARY:")
                prompt_parts.append(profile_data['summary'])
                prompt_parts.append("")
            
            if "skills" in profile_data and profile_data["skills"]:
                prompt_parts.append("SKILLS:")
                for skill in profile_data["skills"]:
                    category = skill.get('category', 'N/A')
                    prompt_parts.append(f"  • {skill['name']} ({category})")
                prompt_parts.append("")
            
            if "experiences" in profile_data and profile_data["experiences"]:
                prompt_parts.append("WORK EXPERIENCE:")
                for exp in profile_data["experiences"]:
                    prompt_parts.append(f"  • {exp['role']} at {exp['company']}")
                    prompt_parts.append(f"    {exp.get('start_date', 'N/A')} - {exp.get('end_date', 'Present')}")
                    if exp.get('description'):
                        prompt_parts.append(f"    {exp['description']}")
                    prompt_parts.append("")
            
            if "projects" in profile_data and profile_data["projects"]:
                prompt_parts.append("PROJECTS:")
                for proj in profile_data["projects"]:
                    prompt_parts.append(f"  • {proj['title']}")
                    if proj.get('description'):
                        prompt_parts.append(f"    {proj['description']}")
                    if proj.get('tech_stack'):
                        tech = ', '.join(proj['tech_stack']) if isinstance(proj['tech_stack'], list) else proj['tech_stack']
                        prompt_parts.append(f"    Technologies: {tech}")
                    prompt_parts.append("")
            
            prompt_parts.append("━" * 80)
        
        if rag_context:
            prompt_parts.append("")
            prompt_parts.append("ADDITIONAL CONTEXT:")
            prompt_parts.append(rag_context)
            prompt_parts.append("")
        
        prompt_parts.append("")
        prompt_parts.append("⚠️  REMINDER: Same language as question, no proficiency levels, include contact info if asked")
        
        return "\n".join(prompt_parts)