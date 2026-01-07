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
        db_session: Session,
        retrieval_pipeline: Optional[RAGRetrievalPipeline] = None,
    ):
        """
        Initialize ProfileAgent.
        
        Args:
            llm_provider: LLM provider for generating responses
            db_session: SQLAlchemy database session
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
    
    # async def _gather_profile_data(
    #     self,
    #     context: RequestContext,
    # ) -> dict:
    #     """
    #     Gather relevant profile data using tools.
        
    #     Args:
    #         context: Request context
            
    #     Returns:
    #         Dictionary with profile data
    #     """
    #     query_lower = context.user_query.lower()
    #     data = {}
        
    #     if any(keyword in query_lower for keyword in ["skill", "yetenek", "teknoloji", "technology", "expertise", "uzmanlık"]):
    #         data["skills"] = await profile_tools.get_profile_skills(
    #             context.profile_id,
    #             self.db_session,
    #         )
        
    #     if any(keyword in query_lower for keyword in ["experience", "deneyim", "work", "iş", "career", "kariyer", "job", "pozisyon"]):
    #         data["experiences"] = await profile_tools.get_profile_experiences(
    #             context.profile_id,
    #             self.db_session,
    #         )
        
    #     if any(keyword in query_lower for keyword in ["project", "proje", "portfolio"]):
    #         data["projects"] = await profile_tools.get_profile_projects(
    #             context.profile_id,
    #             self.db_session,
    #         )
        
    #     if any(keyword in query_lower for keyword in ["summary", "özet", "background", "geçmiş", "about", "hakkında"]):
    #         data["summary"] = await profile_tools.get_profile_summary(
    #             context.profile_id,
    #             self.db_session,
    #         )
        
    #     if not data:
    #         data["basic_info"] = await profile_tools.get_profile_basic_info(
    #             context.profile_id,
    #             self.db_session,
    #         )
    #         data["skills"] = await profile_tools.get_profile_skills(
    #             context.profile_id,
    #             self.db_session,
    #         )
    #         data["experiences"] = await profile_tools.get_profile_experiences(
    #             context.profile_id,
    #             self.db_session,
    #         )
        
    #     return data

    async def _gather_profile_data(self, context: RequestContext) -> dict:
        """TEMP: Mock data for testing without DB"""
        return {
            "summary": "Doğan, modern web teknolojileri ve yapay zeka üzerine uzmanlaşmış bir Backend Mühendisidir.",
            "skills": [
                {"name": "Python"}, 
                {"name": "FastAPI"}, 
                {"name": "PostgreSQL"},
                {"name": "LLM Entegrasyonu"}
            ],
            "experiences": [
                {
                    "role": "Senior Backend Developer", 
                    "company": "AI Tech Solutions", 
                    "start_date": "2021", 
                    "end_date": "Present"
                }
            ],
            "projects": [
                {
                    "title": "Interactive AI CV", 
                    "description": "Agent tabanlı interaktif bir özgeçmiş sistemi."
                }
            ]
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
        
        if profile_data:
            prompt_parts.append("Profile Data:")
            prompt_parts.append("=" * 50)
            
            if "basic_info" in profile_data and profile_data["basic_info"]:
                prompt_parts.append(f"Basic Information: {profile_data['basic_info']}")
            
            if "summary" in profile_data and profile_data["summary"]:
                prompt_parts.append(f"Summary: {profile_data['summary']}")
            
            if "skills" in profile_data and profile_data["skills"]:
                skills_text = ", ".join([s["name"] for s in profile_data["skills"]])
                prompt_parts.append(f"Skills: {skills_text}")
            
            if "experiences" in profile_data and profile_data["experiences"]:
                exp_text = "\n".join([
                    f"- {exp['role']} at {exp['company']} ({exp.get('start_date', '')} - {exp.get('end_date', 'Present')})"
                    for exp in profile_data["experiences"]
                ])
                prompt_parts.append(f"Experiences:\n{exp_text}")
            
            if "projects" in profile_data and profile_data["projects"]:
                projects_text = "\n".join([
                    f"- {proj['title']}: {proj.get('description', '')}"
                    for proj in profile_data["projects"]
                ])
                prompt_parts.append(f"Projects:\n{projects_text}")
            
            prompt_parts.append("")
        
        if rag_context:
            prompt_parts.append("Additional Context (from semantic search):")
            prompt_parts.append("=" * 50)
            prompt_parts.append(rag_context)
            prompt_parts.append("")
        
        prompt_parts.append("Please provide a clear, natural response to the user's question based on the information above.")
        
        return "\n".join(prompt_parts)



