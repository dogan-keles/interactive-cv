"""
GitHub Agent - Handles questions about GitHub repositories and projects.

Priority:
1. Database projects (includes all projects like Rebero)
2. GitHub API repos (supplementary information)
"""

import logging
from typing import Optional, Callable, Dict, List, Any

from sqlalchemy.orm import Session

from backend.infrastructure.llm.provider import BaseLLMProvider
from backend.orchestrator.types import RequestContext, Language
from backend.data_access.vector_db.retrieval import RAGRetrievalPipeline
from backend.tools import github_tools, profile_tools

logger = logging.getLogger(__name__)


def _get_language_name(lang: Language) -> str:
    """Convert language enum to readable name."""
    names = {
        Language.ENGLISH: "English",
        Language.TURKISH: "Turkish",
        Language.KURDISH: "Kurdish",
    }
    return names.get(lang, "English")


class GitHubAgent:
    """
    Agent for handling GitHub and project-related queries.
    
    Strategy:
    - Fetch DB projects first (authoritative, includes all projects)
    - Fetch GitHub repos as supplementary data
    - LLM combines both sources intelligently
    """

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
        """Process GitHub/project-related query."""
        if not self.db_session_factory:
            return "Project data is not available. Database connection is required."

        db = self.db_session_factory()
        
        try:
            project_data = await self._gather_project_data(context, db)
            prompt = self._build_prompt(context, project_data)
            
            response = await self.llm_provider.generate(
                prompt=prompt,
                temperature=0.7,
                max_tokens=1000,
            )
            
            return response.strip()
        
        except Exception as e:
            logger.error(f"GitHubAgent error: {e}", exc_info=True)
            raise
        
        finally:
            db.close()

    async def _gather_project_data(self, context: RequestContext, db: Session) -> Dict[str, Any]:
        """
        Gather project data from both Database and GitHub.
        
        Priority:
        1. Database projects (includes Rebero, etc.)
        2. GitHub repos (supplementary)
        """
        # Get DB projects first (authoritative source)
        db_projects = await profile_tools.get_profile_projects(
            profile_id=context.profile_id,
            db_session=db
        )
        
        # Get GitHub data
        github_username = await github_tools.get_profile_github_username(
            profile_id=context.profile_id,
            db_session=db
        )
        
        github_repos = await github_tools.get_github_repositories(
            profile_id=context.profile_id,
            db_session=db,
            max_repos=15,
            min_stars=0,
            include_forks=False,
        )
        
        logger.info(f"Gathered {len(db_projects or [])} DB projects, "
                   f"{len(github_repos or [])} GitHub repos for {github_username}")
        
        return {
            "db_projects": db_projects or [],
            "github_username": github_username,
            "github_repos": github_repos or [],
        }

    def _build_prompt(
        self,
        context: RequestContext,
        project_data: Dict[str, Any],
    ) -> str:
        """Build comprehensive prompt with DB projects + GitHub repos."""
        lang_name = _get_language_name(context.language)
        
        db_projects = project_data.get("db_projects", [])
        github_repos = project_data.get("github_repos", [])
        username = project_data.get("github_username", "Unknown")
        
        prompt_parts = [
            f"You are a project portfolio assistant for {username}.",
            "",
            f"USER QUESTION: {context.user_query}",
            f"RESPOND IN: {lang_name}",
            "",
            "=" * 60,
            "PROJECT DATA (use this to answer):",
            "=" * 60,
            "",
        ]
        
        # DATABASE PROJECTS (Priority 1 - Most Important)
        if db_projects:
            prompt_parts.append("📋 FEATURED PROJECTS (from portfolio database):")
            prompt_parts.append("These are the PRIMARY projects - use these first!")
            prompt_parts.append("")
            
            for i, proj in enumerate(db_projects, 1):
                prompt_parts.append(f"{i}. **{proj.get('title', 'Untitled')}**")
                
                if proj.get('description'):
                    prompt_parts.append(f"   Description: {proj['description']}")
                
                if proj.get('tech_stack'):
                    tech = proj['tech_stack']
                    tech_str = ', '.join(str(t) for t in tech) if isinstance(tech, list) else str(tech)
                    prompt_parts.append(f"   Tech Stack: {tech_str}")
                
                if proj.get('demo_url'):
                    prompt_parts.append(f"   Live Demo: {proj['demo_url']}")
                
                if proj.get('github_url'):
                    prompt_parts.append(f"   GitHub: {proj['github_url']}")
                
                prompt_parts.append("")
        
        # GITHUB REPOSITORIES (Supplementary)
        if github_repos:
            prompt_parts.append("=" * 60)
            prompt_parts.append(f"💻 GITHUB REPOSITORIES (username: {username}):")
            prompt_parts.append("These are supplementary - use to show coding activity")
            prompt_parts.append("=" * 60)
            prompt_parts.append("")
            
            top_repos = github_repos[:5]
            
            for i, repo in enumerate(top_repos, 1):
                stars = repo.get('stargazers_count', 0)
                metrics = f"({stars} stars)" if stars > 0 else "(Featured)"
                
                prompt_parts.append(f"{i}. **{repo['name']}** {metrics}")
                
                if repo.get('description'):
                    prompt_parts.append(f"   {repo['description']}")
                
                languages = repo.get('languages', [])
                if languages:
                    prompt_parts.append(f"   Languages: {', '.join(languages)}")
                
                prompt_parts.append(f"   URL: {repo['html_url']}")
                prompt_parts.append("")
            
            if len(github_repos) > 5:
                remaining = [r['name'] for r in github_repos[5:]]
                prompt_parts.append(f"...and {len(remaining)} more repositories: {', '.join(remaining[:5])}")
                prompt_parts.append("")
        
        # No data at all
        if not db_projects and not github_repos:
            prompt_parts.append("No project data available.")
            prompt_parts.append("")
        
        # Instructions
        prompt_parts.extend([
            "=" * 60,
            "INSTRUCTIONS:",
            "=" * 60,
            "1. PRIORITIZE database projects - they are curated and complete",
            "2. Use GitHub repos as supplementary evidence of coding activity",
            "3. If user asks about a specific project (e.g., Rebero), check DB projects FIRST",
            "4. Focus on what projects DO and their technical achievements",
            "5. If a project has few/no GitHub stars, emphasize innovation and complexity",
            "6. Be concise, technical, and helpful",
            f"7. Respond in {lang_name}",
            "",
        ])
        
        return "\n".join(prompt_parts)