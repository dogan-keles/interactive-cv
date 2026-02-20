"""
Profile Agent - Handles questions about professional skills, experience, and background.
"""

import logging
import re
from typing import Optional, Callable

from sqlalchemy.orm import Session

from backend.infrastructure.llm.provider import BaseLLMProvider
from backend.orchestrator.types import RequestContext, Language
from backend.data_access.vector_db.retrieval import RAGRetrievalPipeline
from backend.tools import profile_tools

logger = logging.getLogger(__name__)


def _get_language_name(lang: Language) -> str:
    """Convert language enum to readable name."""
    names = {
        Language.AUTO: "English",
        Language.ENGLISH: "English",
        Language.TURKISH: "Turkish",
        Language.KURDISH: "Kurdish",
        Language.GERMAN: "German",
        Language.FRENCH: "French",
        Language.SPANISH: "Spanish",
        Language.ITALIAN: "Italian",
        Language.PORTUGUESE: "Portuguese",
        Language.RUSSIAN: "Russian",
        Language.ARABIC: "Arabic",
        Language.CHINESE: "Chinese",
        Language.JAPANESE: "Japanese",
        Language.KOREAN: "Korean",
    }
    return names.get(lang, "English")


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
            
            system_prompt = self._build_system_prompt(context)
            user_prompt = self._build_user_prompt(context, profile_data, rag_context)
            
            response = await self.llm_provider.generate(
                prompt=user_prompt,
                system_prompt=system_prompt,
                temperature=0.3,
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
            # Try both possible method names for compatibility
            if hasattr(self.retrieval_pipeline, 'retrieve'):
                rag_context = await self.retrieval_pipeline.retrieve(
                    query=context.user_query,
                    profile_id=context.profile_id,
                    top_k=3,
                    min_score=0.3,
                )
            elif hasattr(self.retrieval_pipeline, 'retrieve_context'):
                rag_context = await self.retrieval_pipeline.retrieve_context(
                    query=context.user_query,
                    profile_id=context.profile_id,
                    top_k=3,
                    min_score=0.3,
                )
            else:
                logger.warning("RAG pipeline has no retrieve or retrieve_context method")
                return None
            
            return rag_context if rag_context else None
        except Exception as e:
            logger.warning(f"RAG retrieval failed: {e}")
            return None
    
    def _build_system_prompt(self, context: RequestContext) -> str:
        """Build system prompt with strict language enforcement."""
        lang_name = _get_language_name(context.language)
        
        return f"""You are a professional CV assistant for Doğan Keleş.

ABSOLUTE RULES YOU MUST FOLLOW:
1. RESPOND ONLY IN {lang_name.upper()}. Every single word must be in {lang_name}. No exceptions.
2. ONLY use information from the profile data provided. Never invent or guess anything.
3. Always call the candidate "Doğan" or "Doğan Keleş" (never "Don", "Doğn", or "the candidate").
4. Do NOT mention proficiency levels (no "expert", "advanced", "proficient", "beginner").
5. Keep answers concise and well-organized.
6. If information is not in the provided data, say so honestly.

YOU ARE RESPONDING IN: {lang_name.upper()}"""
    
    def _build_user_prompt(
        self,
        context: RequestContext,
        profile_data: dict,
        rag_context: Optional[str],
    ) -> str:
        """Build user prompt with profile data."""
        lang_name = _get_language_name(context.language)
        
        prompt_parts = [
            f"Question: {context.user_query}",
            "",
            "---",
            "PROFILE DATA (use ONLY this data to answer):",
            "---",
        ]
        
        if profile_data:
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
                    prompt_parts.append(f"  - {skill['name']} ({category})")
                prompt_parts.append("")
            
            if "experiences" in profile_data and profile_data["experiences"]:
                prompt_parts.append("WORK EXPERIENCE:")
                for exp in profile_data["experiences"]:
                    prompt_parts.append(f"  - {exp['role']} at {exp['company']}")
                    prompt_parts.append(f"    {exp.get('start_date', 'N/A')} - {exp.get('end_date', 'Present')}")
                    if exp.get('description'):
                        prompt_parts.append(f"    {exp['description']}")
                    prompt_parts.append("")
            
            if "projects" in profile_data and profile_data["projects"]:
                prompt_parts.append("PROJECTS:")
                for proj in profile_data["projects"]:
                    prompt_parts.append(f"  - {proj['title']}")
                    if proj.get('description'):
                        prompt_parts.append(f"    {proj['description']}")
                    if proj.get('tech_stack'):
                        tech = ', '.join(proj['tech_stack']) if isinstance(proj['tech_stack'], list) else proj['tech_stack']
                        prompt_parts.append(f"    Technologies: {tech}")
                    prompt_parts.append("")
        
        if rag_context:
            prompt_parts.append("ADDITIONAL CONTEXT:")
            prompt_parts.append(rag_context)
            prompt_parts.append("")
        
        prompt_parts.append("---")
        prompt_parts.append(f"Answer the question above using ONLY the profile data. Respond in {lang_name}.")
        
        return "\n".join(prompt_parts)