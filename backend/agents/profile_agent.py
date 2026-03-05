"""
Profile Agent - Handles questions about professional skills, experience, and background.
"""

import logging
import re
from typing import Optional, Callable, Dict, List, Any
from collections import defaultdict

from sqlalchemy.orm import Session

from backend.infrastructure.llm.provider import BaseLLMProvider
from backend.orchestrator.types import RequestContext, Language
from backend.data_access.vector_db.retrieval import RAGRetrievalPipeline
from backend.tools import profile_tools

logger = logging.getLogger(__name__)


def _get_language_name(lang: Language) -> str:
    """Convert language enum to readable name."""
    names = {
        Language.AUTO: "English", Language.ENGLISH: "English", Language.TURKISH: "Turkish",
        Language.KURDISH: "Kurdish", Language.GERMAN: "German", Language.FRENCH: "French",
        Language.SPANISH: "Spanish", Language.ITALIAN: "Italian", Language.PORTUGUESE: "Portuguese",
        Language.RUSSIAN: "Russian", Language.ARABIC: "Arabic", Language.CHINESE: "Chinese",
        Language.JAPANESE: "Japanese", Language.KOREAN: "Korean",
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
        cleaned = response
        for pattern in [r'\bproficiency in\b', r'\bproficient in\b']:
            cleaned = re.sub(pattern, '', cleaned, flags=re.IGNORECASE)
        return re.sub(r'\s+', ' ', cleaned).strip()
    
    async def _gather_profile_data(self, context: RequestContext) -> Dict[str, Any]:
        """Gather all profile data - let LLM decide what's relevant."""
        if not self.db_session_factory:
            return {}
        
        db = self.db_session_factory()
        
        try:
            data = {
                "basic_info": await profile_tools.get_profile_basic_info(context.profile_id, db),
                "summary": await profile_tools.get_profile_summary(context.profile_id, db),
                "skills": await profile_tools.get_profile_skills(context.profile_id, db),
                "experiences": await profile_tools.get_profile_experiences(context.profile_id, db),
                "projects": await profile_tools.get_profile_projects(context.profile_id, db),
            }
            
            logger.info(f"Gathered profile data: {len(data.get('skills', []))} skills, "
                       f"{len(data.get('experiences', []))} experiences, "
                       f"{len(data.get('projects', []))} projects")
            
            return data
        finally:
            db.close()
    
    async def _get_rag_context(self, context: RequestContext) -> Optional[str]:
        """Get RAG context via semantic search."""
        if not self.retrieval_pipeline or context.rag_context:
            return context.rag_context
        
        try:
            if hasattr(self.retrieval_pipeline, 'retrieve'):
                return await self.retrieval_pipeline.retrieve(
                    query=context.user_query,
                    profile_id=context.profile_id,
                    top_k=3,
                    min_score=0.3,
                )
            elif hasattr(self.retrieval_pipeline, 'retrieve_context'):
                return await self.retrieval_pipeline.retrieve_context(
                    query=context.user_query,
                    profile_id=context.profile_id,
                    top_k=3,
                    min_score=0.3,
                )
        except Exception as e:
            logger.warning(f"RAG retrieval failed: {e}")
        
        return None
    
    def _build_system_prompt(self, context: RequestContext) -> str:
        """Build system prompt with LLM instructions."""
        lang_name = _get_language_name(context.language)
        
        return f"""You are a professional CV assistant for Doğan Keleş.

CRITICAL RULES:
1. Respond ONLY in {lang_name.upper()}.
2. Use ONLY the provided profile data. Never invent information.
3. When asked about a specific company/project, focus ONLY on that item.
4. Use "Doğan" or "Doğan Keleş" (never "the candidate").
5. Do NOT mention proficiency levels.

⚠️  SKILL LISTING RULE (VERY IMPORTANT):
When asked about skills, you MUST use the category summaries from the data.
CORRECT: "Backend: Python, Java, Spring Boot (+5 more), Database: PostgreSQL, Redis (+3 more)"
WRONG: Listing all 64 skills individually like "Python, Java, Spring Boot, ASP.NET, Node.js..."

Use the format provided in the data. If a category has "+X more", keep it that way.

6. If information is missing, say so honestly.

YOU ARE RESPONDING IN: {lang_name.upper()}"""
    
    def _build_user_prompt(
        self,
        context: RequestContext,
        profile_data: Dict[str, Any],
        rag_context: Optional[str],
    ) -> str:
        """Build user prompt with all profile data."""
        lang_name = _get_language_name(context.language)
        
        prompt_parts = [
            f"Question: {context.user_query}",
            "",
            "---",
            "PROFILE DATA:",
            "---",
        ]
        
        # Basic info
        if profile_data.get("basic_info"):
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
        
        # Summary
        if profile_data.get("summary"):
            prompt_parts.append("SUMMARY:")
            prompt_parts.append(str(profile_data['summary']))
            prompt_parts.append("")
        
        # Skills (grouped by category with smart summarization)
        if profile_data.get("skills"):
            skills_by_cat = defaultdict(list)
            for skill in profile_data["skills"]:
                skills_by_cat[skill.get('category', 'Other')].append(skill['name'])
            
            prompt_parts.append("SKILLS (use these category summaries when answering):")
            for cat, skills_list in sorted(skills_by_cat.items()):
                if len(skills_list) > 10:
                    shown = ', '.join(skills_list[:10])
                    prompt_parts.append(f"  {cat}: {shown} (+{len(skills_list)-10} more)")
                else:
                    prompt_parts.append(f"  {cat}: {', '.join(skills_list)}")
            prompt_parts.append("")
        
        # Experiences
        if profile_data.get("experiences"):
            prompt_parts.append("WORK EXPERIENCE:")
            for exp in profile_data["experiences"]:
                prompt_parts.append(f"  Company: {exp['company']}")
                prompt_parts.append(f"  Role: {exp['role']}")
                prompt_parts.append(f"  Period: {exp.get('start_date', 'N/A')} - {exp.get('end_date', 'Present')}")
                if exp.get('location'):
                    prompt_parts.append(f"  Location: {exp['location']}")
                if exp.get('description'):
                    prompt_parts.append(f"  Details: {str(exp['description'])}")
                prompt_parts.append("")
        
        # Projects
        if profile_data.get("projects"):
            prompt_parts.append("PROJECTS:")
            for proj in profile_data["projects"]:
                prompt_parts.append(f"  - {proj['title']}")
                if proj.get('description'):
                    prompt_parts.append(f"    {str(proj['description'])}")
                if proj.get('tech_stack'):
                    tech = proj['tech_stack']
                    tech_str = ', '.join(str(t) for t in tech) if isinstance(tech, list) else str(tech)
                    prompt_parts.append(f"    Tech: {tech_str}")
                if proj.get('demo_url'):
                    prompt_parts.append(f"    URL: {proj['demo_url']}")
                prompt_parts.append("")
        
        # RAG context
        if rag_context:
            prompt_parts.append("ADDITIONAL CONTEXT:")
            prompt_parts.append(str(rag_context))
            prompt_parts.append("")
        
        prompt_parts.append("---")
        prompt_parts.append(f"Answer the question using ONLY the data above. Respond in {lang_name}.")
        prompt_parts.append("REMEMBER: For skills, use the category summaries format shown above!")
        
        return "\n".join(str(part) for part in prompt_parts)