"""
Profile Agent implementation - OPTIMIZED VERSION

Handles questions about professional skills, experience, and background.
Uses profile tools and optional semantic search to retrieve data.

OPTIMIZATIONS:
- Post-processing to fix language mixing ("siguientes", "quite", etc.)
- Contact info included in responses
- Removed skill level mentions
- Thread-safe session management
"""

import logging
import re
from typing import Optional, Callable

from sqlalchemy.orm import Session

from backend.infrastructure.llm.provider import BaseLLMProvider
from backend.orchestrator.types import RequestContext, Language
from backend.data_access.vector_db.retrieval import RAGRetrievalPipeline
from backend.agents.prompts import (
    PROFILE_AGENT_SYSTEM_PROMPT,
    PROFILE_AGENT_INSTRUCTIONS,
    get_language_instruction,
)
from backend.tools import profile_tools
from backend.tools import semantic_search_tools

logger = logging.getLogger(__name__)


class ProfileAgent:
    """
    Agent for handling profile-related queries.
    
    Answers questions about skills, experience, background, and expertise.
    Uses SQL-based profile tools and optional semantic search.
    """
    
    def __init__(
        self,
        llm_provider: BaseLLMProvider,
        db_session_factory: Optional[Callable[[], Session]] = None,
        retrieval_pipeline: Optional[RAGRetrievalPipeline] = None,
    ):
        """
        Initialize ProfileAgent.
        
        Args:
            llm_provider: LLM provider for generating responses
            db_session_factory: Factory function to create database sessions (e.g., SessionLocal)
            retrieval_pipeline: Optional RAG retrieval pipeline for semantic search
        """
        self.llm_provider = llm_provider
        self.db_session_factory = db_session_factory
        self.retrieval_pipeline = retrieval_pipeline
    
    async def process(self, context: RequestContext) -> str:
        """
        Process profile-related query.
        
        Args:
            context: Request context with user query, profile_id, language, etc.
            
        Returns:
            Agent response in the detected language
        """
        try:
            profile_data = await self._gather_profile_data(context)
            rag_context = await self._get_rag_context(context)
            
            prompt = self._build_prompt(context, profile_data, rag_context)
            
            response = await self.llm_provider.generate(
                prompt=prompt,
                temperature=0.7,
                max_tokens=1000,
            )
            
            # Post-process response to fix language issues
            cleaned_response = self._clean_response(response.strip(), context.language)
            
            return cleaned_response
        
        except Exception as e:
            logger.error(f"ProfileAgent error processing query: {e}", exc_info=True)
            raise
    
    def _clean_response(self, response: str, language: Language) -> str:
        """
        Clean response to fix language mixing issues.
        
        Args:
            response: Raw response from LLM
            language: Target language
            
        Returns:
            Cleaned response
        """
        # Fix Spanish words in Turkish/English responses
        replacements = {
            "siguientes": {
                Language.TURKISH: "şu",
                Language.ENGLISH: "following",
                Language.KURDISH: "ev",
            },
            "siguiente": {
                Language.TURKISH: "şu",
                Language.ENGLISH: "following",
                Language.KURDISH: "ev",
            },
            # Fix English words in Turkish
            "quite": {
                Language.TURKISH: "oldukça",
            },
            "following": {
                Language.TURKISH: "şu",
                Language.KURDISH: "ev",
            },
        }
        
        cleaned = response
        
        for word, lang_replacements in replacements.items():
            if language in lang_replacements:
                # Case-insensitive replacement
                pattern = re.compile(re.escape(word), re.IGNORECASE)
                cleaned = pattern.sub(lang_replacements[language], cleaned)
        
        # Remove "proficiency" mentions
        proficiency_patterns = [
            r'\bproficiency in\b',
            r'\bproficient in\b',
            r'\b- proficient\b',
            r'\buzmanlık seviyem\b',
            r'\bproficiency level\b',
        ]
        
        for pattern in proficiency_patterns:
            cleaned = re.sub(pattern, '', cleaned, flags=re.IGNORECASE)
        
        # Clean up extra spaces
        cleaned = re.sub(r'\s+', ' ', cleaned)
        cleaned = cleaned.strip()
        
        return cleaned
    
    async def _gather_profile_data(
        self,
        context: RequestContext,
    ) -> dict:
        """
        Gather relevant profile data using tools.
        
        Args:
            context: Request context
            
        Returns:
            Dictionary with profile data
        """
        # If no database session factory, return fallback
        if not self.db_session_factory:
            logger.warning("No database session factory available - using fallback")
            return self._get_fallback_data()
        
        # Create temporary session for this request
        db = self.db_session_factory()
        
        try:
            query_lower = context.user_query.lower()
            data = {}
            
            # Contact info queries
            if any(keyword in query_lower for keyword in [
                "contact", "email", "reach", "iletişim", "e-posta", "ulaş",
                "peywendî", "email"  # Kurdish
            ]):
                data["basic_info"] = await profile_tools.get_profile_basic_info(
                    context.profile_id,
                    db,
                )
            
            # Skill-related queries
            if any(keyword in query_lower for keyword in [
                "skill", "yetenek", "teknoloji", "technology", 
                "expertise", "uzmanlık", "know", "biliyor", "can",
                "dizane", "jêhatî"  # Kurdish
            ]):
                data["skills"] = await profile_tools.get_profile_skills(
                    context.profile_id,
                    db,
                )
            
            # Experience-related queries
            if any(keyword in query_lower for keyword in [
                "experience", "deneyim", "work", "iş", "career", 
                "kariyer", "job", "pozisyon", "company", "şirket", "worked",
                "kar", "ezmûn"  # Kurdish
            ]):
                data["experiences"] = await profile_tools.get_profile_experiences(
                    context.profile_id,
                    db,
                )
            
            # Project-related queries
            if any(keyword in query_lower for keyword in [
                "project", "proje", "portfolio", "built", "created", "developed",
                "proje", "çalışma"  # Kurdish
            ]):
                data["projects"] = await profile_tools.get_profile_projects(
                    context.profile_id,
                    db,
                )
            
            # Summary/general queries
            if any(keyword in query_lower for keyword in [
                "summary", "özet", "background", "geçmiş", 
                "about", "hakkında", "who", "kim", "tell me", "yourself",
                "çi", "kî"  # Kurdish
            ]):
                data["summary"] = await profile_tools.get_profile_summary(
                    context.profile_id,
                    db,
                )
            
            # If no specific keywords, get general info
            if not data:
                data["basic_info"] = await profile_tools.get_profile_basic_info(
                    context.profile_id,
                    db,
                )
                data["summary"] = await profile_tools.get_profile_summary(
                    context.profile_id,
                    db,
                )
                data["skills"] = await profile_tools.get_profile_skills(
                    context.profile_id,
                    db,
                )
            
            # If database returned nothing, inform the user
            if not any(data.values()):
                logger.info(f"No profile data found for profile_id: {context.profile_id}")
            
            return data
        
        finally:
            # Always close the session
            db.close()
    
    def _get_fallback_data(self) -> dict:
        """Fallback mock data when no database is available."""
        logger.warning("Using fallback mock data - database not connected")
        return {
            "summary": "Profile data is currently unavailable. Please ensure the database is configured.",
            "skills": [],
            "experiences": [],
            "projects": []
        }
    
    async def _get_rag_context(
        self,
        context: RequestContext,
    ) -> Optional[str]:
        """
        Get RAG context via semantic search if available.
        """
        if not self.retrieval_pipeline:
            return None
        
        # If context already has RAG context, use it
        if context.rag_context:
            return context.rag_context
        
        try:
            # Call retrieval pipeline directly
            rag_context = await self.retrieval_pipeline.retrieve_context(
                query=context.user_query,
                profile_id=context.profile_id,
                top_k=3,  # Get top 3 most relevant chunks
                min_score=0.3,  # 30% similarity minimum
            )
            return rag_context if rag_context else None
        except AttributeError as e:
            logger.warning(f"RAG retrieval method not found: {e}")
            return None
        except Exception as e:
            logger.warning(f"RAG retrieval failed: {e}")
            return None
    
    def _build_prompt(
        self,
        context: RequestContext,
        profile_data: dict,
        rag_context: Optional[str],
    ) -> str:
        """
        Build complete prompt for LLM.
        
        Args:
            context: Request context
            profile_data: Gathered profile data
            rag_context: Optional RAG context
            
        Returns:
            Complete prompt string
        """
        prompt_parts = [
            PROFILE_AGENT_SYSTEM_PROMPT,
            "",
            PROFILE_AGENT_INSTRUCTIONS,
            "",
            "=" * 80,
            "USER'S QUESTION (DETECT THE LANGUAGE FROM THIS):",
            "",
            f'"{context.user_query}"',
            "",
            "=" * 80,
            "",
            "⚠️  YOU MUST RESPOND IN THE SAME LANGUAGE AS THE QUESTION ABOVE ⚠️",
            "⚠️  DO NOT MIX LANGUAGES - Use ONLY the question's language ⚠️",
            "⚠️  NO Spanish words in Turkish/English! NO English words in Turkish! ⚠️",
            "",
        ]
        
        # Check if we have any data
        has_data = any(profile_data.values()) if profile_data else False
        
        if has_data:
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
                prompt_parts.append("SKILLS (do NOT mention proficiency levels):")
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
                    if exp.get('location'):
                        prompt_parts.append(f"    Location: {exp['location']}")
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
                    if proj.get('github_url'):
                        prompt_parts.append(f"    GitHub: {proj['github_url']}")
                    prompt_parts.append("")
            
            prompt_parts.append("━" * 80)
            prompt_parts.append("")
        else:
            # No data available
            prompt_parts.append("⚠️  NO PROFILE DATA AVAILABLE IN DATABASE")
            prompt_parts.append("Inform the user politely that profile information is not yet available.")
            prompt_parts.append("")
        
        if rag_context:
            prompt_parts.append("ADDITIONAL CONTEXT (from semantic search):")
            prompt_parts.append("━" * 80)
            prompt_parts.append(rag_context)
            prompt_parts.append("━" * 80)
            prompt_parts.append("")
        
        prompt_parts.append("NOW PROVIDE YOUR ANSWER:")
        prompt_parts.append("━" * 80)
        prompt_parts.append("⚠️  FINAL REMINDER: Use the SAME LANGUAGE as the user's question!")
        prompt_parts.append("⚠️  DO NOT say 'proficiency' or 'proficient' or skill levels!")
        prompt_parts.append("⚠️  For contact questions: Include email (dgnkls.47@gmail.com) and LinkedIn!")
        prompt_parts.append("Be professional, accurate, concise, and helpful.")
        prompt_parts.append("")
        
        return "\n".join(prompt_parts)