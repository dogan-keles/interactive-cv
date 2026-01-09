"""
Profile Agent implementation.

Handles questions about professional skills, experience, and background.
Uses profile tools and optional semantic search to retrieve data.
"""

import logging
from typing import Optional

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
        db_session: Optional[Session] = None,
        retrieval_pipeline: Optional[RAGRetrievalPipeline] = None,
    ):
        """
        Initialize ProfileAgent.
        
        Args:
            llm_provider: LLM provider for generating responses
            db_session: SQLAlchemy database session (optional)
            retrieval_pipeline: Optional RAG retrieval pipeline for semantic search
        """
        self.llm_provider = llm_provider
        self.db_session = db_session
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
            
            return response.strip()
        
        except Exception as e:
            logger.error(f"ProfileAgent error processing query: {e}", exc_info=True)
            raise
    
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
        # If no database session, return empty
        if not self.db_session:
            logger.warning("No database session available - using fallback")
            return self._get_fallback_data()
        
        query_lower = context.user_query.lower()
        data = {}
        
        # Skill-related queries
        if any(keyword in query_lower for keyword in [
            "skill", "yetenek", "teknoloji", "technology", 
            "expertise", "uzmanlık", "know", "biliyor", "can"
        ]):
            data["skills"] = await profile_tools.get_profile_skills(
                context.profile_id,
                self.db_session,
            )
        
        # Experience-related queries
        if any(keyword in query_lower for keyword in [
            "experience", "deneyim", "work", "iş", "career", 
            "kariyer", "job", "pozisyon", "company", "şirket", "worked"
        ]):
            data["experiences"] = await profile_tools.get_profile_experiences(
                context.profile_id,
                self.db_session,
            )
        
        # Project-related queries
        if any(keyword in query_lower for keyword in [
            "project", "proje", "portfolio", "built", "created", "developed"
        ]):
            data["projects"] = await profile_tools.get_profile_projects(
                context.profile_id,
                self.db_session,
            )
        
        # Summary/general queries
        if any(keyword in query_lower for keyword in [
            "summary", "özet", "background", "geçmiş", 
            "about", "hakkında", "who", "kim", "tell me"
        ]):
            data["summary"] = await profile_tools.get_profile_summary(
                context.profile_id,
                self.db_session,
            )
        
        # If no specific keywords, get general info
        if not data:
            data["basic_info"] = await profile_tools.get_profile_basic_info(
                context.profile_id,
                self.db_session,
            )
            data["summary"] = await profile_tools.get_profile_summary(
                context.profile_id,
                self.db_session,
            )
            data["skills"] = await profile_tools.get_profile_skills(
                context.profile_id,
                self.db_session,
            )
        
        # If database returned nothing, inform the user
        if not any(data.values()):
            logger.info(f"No profile data found for profile_id: {context.profile_id}")
        
        return data
    
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
        
        Args:
            context: Request context
            
        Returns:
            Formatted context string or None
        """
        if not self.retrieval_pipeline:
            return None
        
        if context.rag_context:
            return context.rag_context
        
        try:
            rag_context = await semantic_search_tools.semantic_search_with_context(
                query=context.user_query,
                profile_id=context.profile_id,
                retrieval_pipeline=self.retrieval_pipeline,
                top_k=5,
                max_context_length=2000,
            )
            return rag_context if rag_context else None
        except Exception as e:
            logger.warning(f"Semantic search failed: {e}")
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
            get_language_instruction(context.language),
            "",
            f"User Query: {context.user_query}",
            f"Profile ID: {context.profile_id}",
            "",
        ]
        
        # Check if we have any data
        has_data = any(profile_data.values()) if profile_data else False
        
        if has_data:
            prompt_parts.append("Profile Data:")
            prompt_parts.append("=" * 50)
            
            if "basic_info" in profile_data and profile_data["basic_info"]:
                info = profile_data["basic_info"]
                prompt_parts.append(f"Name: {info.get('name', 'N/A')}")
                prompt_parts.append(f"Email: {info.get('email', 'N/A')}")
                prompt_parts.append(f"Location: {info.get('location', 'N/A')}")
                if info.get('linkedin_url'):
                    prompt_parts.append(f"LinkedIn: {info['linkedin_url']}")
                if info.get('github_username'):
                    prompt_parts.append(f"GitHub: {info['github_username']}")
            
            if "summary" in profile_data and profile_data["summary"]:
                prompt_parts.append(f"\nSummary: {profile_data['summary']}")
            
            if "skills" in profile_data and profile_data["skills"]:
                skills_text = ", ".join([
                    f"{s['name']} ({s.get('proficiency_level', 'N/A')})" 
                    for s in profile_data["skills"]
                ])
                prompt_parts.append(f"\nSkills: {skills_text}")
            
            if "experiences" in profile_data and profile_data["experiences"]:
                prompt_parts.append("\nExperiences:")
                for exp in profile_data["experiences"]:
                    prompt_parts.append(
                        f"- {exp['role']} at {exp['company']} "
                        f"({exp.get('start_date', 'N/A')} - {exp.get('end_date', 'Present')})"
                    )
                    if exp.get('description'):
                        prompt_parts.append(f"  {exp['description']}")
            
            if "projects" in profile_data and profile_data["projects"]:
                prompt_parts.append("\nProjects:")
                for proj in profile_data["projects"]:
                    prompt_parts.append(f"- {proj['title']}")
                    if proj.get('description'):
                        prompt_parts.append(f"  {proj['description']}")
                    if proj.get('tech_stack'):
                        tech = ', '.join(proj['tech_stack']) if isinstance(proj['tech_stack'], list) else proj['tech_stack']
                        prompt_parts.append(f"  Tech: {tech}")
            
            prompt_parts.append("")
        else:
            # No data available
            prompt_parts.append("⚠️ No profile data found in database.")
            prompt_parts.append("Please inform the user politely that the profile information is not yet available.")
            prompt_parts.append("")
        
        if rag_context:
            prompt_parts.append("Additional Context (from semantic search):")
            prompt_parts.append("=" * 50)
            prompt_parts.append(rag_context)
            prompt_parts.append("")
        
        prompt_parts.append("Please provide a clear, natural response to the user's question based on the information above.")
        
        return "\n".join(prompt_parts)