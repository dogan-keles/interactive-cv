"""
GitHub Agent implementation - FIXED VERSION

Handles questions about GitHub repositories, projects, and tech stack.
Uses github_tools and optional semantic search to retrieve data.

CHANGES:
- Uses session factory instead of global session (thread-safe)
- Creates and closes sessions properly for each request
"""

import logging
from typing import Optional, Callable

from sqlalchemy.orm import Session

from backend.infrastructure.llm.provider import BaseLLMProvider
from backend.orchestrator.types import RequestContext
from backend.data_access.vector_db.retrieval import RAGRetrievalPipeline
from backend.tools import github_tools

logger = logging.getLogger(__name__)


class GitHubAgent:
    """
    Agent for handling GitHub-related queries.
    
    Retrieves repository data from GitHub API and presents
    the most important projects with their tech stacks.
    """

    def __init__(
        self,
        llm_provider: BaseLLMProvider,
        db_session_factory: Optional[Callable[[], Session]] = None,
        retrieval_pipeline: Optional[RAGRetrievalPipeline] = None,
    ):
        """
        Initialize GitHub Agent.
        
        Args:
            llm_provider: LLM provider for generating responses
            db_session_factory: Factory function to create database sessions (e.g., SessionLocal)
            retrieval_pipeline: Optional RAG pipeline for semantic search
        """
        self.llm_provider = llm_provider
        self.db_session_factory = db_session_factory
        self.retrieval_pipeline = retrieval_pipeline

    async def process(self, context: RequestContext) -> str:
        """
        Process GitHub-related query.
        
        Args:
            context: Request context with user query, profile_id, language
            
        Returns:
            Agent response about GitHub repositories
        """
        if self.db_session_factory is None:
            return "GitHub data is not available. Database connection is required."

        # Create temporary session for this request
        db = self.db_session_factory()
        
        try:
            # Gather GitHub data
            github_data = await self._gather_github_data(context, db)
            
            # Build prompt with repository information
            prompt = self._build_prompt(context, github_data)
            
            # Generate response
            response = await self.llm_provider.generate(
                prompt=prompt,
                temperature=0.7,
                max_tokens=1000,
            )
            
            return response.strip()
        
        except Exception as e:
            logger.error(f"GitHubAgent error processing query: {e}", exc_info=True)
            raise
        
        finally:
            # Always close the session
            db.close()

    async def _gather_github_data(self, context: RequestContext, db: Session) -> dict:
        """
        Gather GitHub repository data.
        
        Args:
            context: Request context
            db: Database session
            
        Returns:
            Dictionary with username and repositories
        """
        return {
            "username": await github_tools.get_profile_github_username(
                profile_id=context.profile_id,
                db_session=db,
            ),
            "repositories": await github_tools.get_github_repositories(
                profile_id=context.profile_id,
                db_session=db,
                max_repos=15,  # Top 15 most important
                min_stars=0,
                include_forks=False,
            ),
        }

    def _build_prompt(
        self,
        context: RequestContext,
        github_data: dict,
    ) -> str:
        """
        Build prompt for LLM with GitHub data context.
        
        Args:
            context: Request context
            github_data: GitHub repositories data
            
        Returns:
            Formatted prompt string
        """
        repos = github_data.get("repositories", [])
        username = github_data.get("username", "Unknown")
        
        if not repos:
            return f"""You are a GitHub portfolio assistant.

USER QUERY: {context.user_query}
LANGUAGE: Respond in {context.language.value}

No GitHub repositories found for this profile.
"""
        
        # Build detailed prompt with top repos highlighted
        prompt = f"""You are a GitHub portfolio assistant presenting the candidate's most important projects.

USER QUERY: {context.user_query}
LANGUAGE: Respond in {context.language.value}

GITHUB USERNAME: {username}
FEATURED PROJECTS: Showing {len(repos)} most relevant repositories
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
TOP PROJECTS (sorted by importance - stars, activity, size):
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

"""
        
        # Show top projects with full details
        top_count = min(5, len(repos))
        
        for i, repo in enumerate(repos[:top_count], 1):
            # Format tech stack
            languages = repo.get("languages", [])
            if not languages and repo.get("language"):
                languages = [repo.get("language")]
            tech_stack = ", ".join(languages) if languages else "Not specified"
            
            # Format topics/tags
            topics = repo.get("topics", [])
            topics_str = ", ".join(topics) if topics else "None"
            
            # Format stars and forks
            stars = repo.get("stargazers_count", 0)
            forks = repo.get("forks_count", 0)
            
            # Visual star rating (max 5 stars)
            # Don't emphasize metrics for low-star projects
            star_display = "⭐" * min(stars, 5) if stars > 3 else ""
            
            # Only show metrics if significant
            if stars > 0 or forks > 0:
                metrics = f"({stars} stars, {forks} forks)"
            else:
                metrics = "(Showcase project)"
            
            prompt += f"""
{i}. **{repo['name']}** {star_display} {metrics}
   📝 Description: {repo['description']}
   💻 Tech Stack: {tech_stack}
   🏷️  Topics: {topics_str}
   🔗 URL: {repo['html_url']}
   📅 Last Updated: {repo.get('updated_at', 'N/A')[:10]}

"""
        
        # If more repos, summarize them by tech stack
        if len(repos) > top_count:
            remaining = repos[top_count:]
            prompt += f"""━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
ADDITIONAL PROJECTS ({len(remaining)}):
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

"""
            # Group by language
            by_language = {}
            for repo in remaining:
                lang = repo.get("language", "Other")
                if lang not in by_language:
                    by_language[lang] = []
                by_language[lang].append(repo["name"])
            
            for lang, repos_list in by_language.items():
                prompt += f"**{lang}**: {', '.join(repos_list[:5])}"
                if len(repos_list) > 5:
                    prompt += f" (+{len(repos_list) - 5} more)"
                prompt += "\n"
        
        # Add tech stack summary
        all_languages = set()
        all_topics = set()
        for repo in repos:
            all_languages.update(repo.get("languages", []))
            all_topics.update(repo.get("topics", []))
        
        prompt += f"""
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
OVERALL TECH STACK SUMMARY:
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

Languages/Frameworks: {', '.join(sorted(all_languages)) if all_languages else 'Various'}
Key Topics: {', '.join(sorted(all_topics)[:10]) if all_topics else 'Various'}

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

INSTRUCTIONS FOR YOUR RESPONSE:
1. Focus on answering the user's specific question
2. Highlight the MOST RELEVANT projects for their query
3. Focus on what the projects DO and their technical features (NOT on star/fork counts)
4. If a project has few or no stars, emphasize its innovation, complexity, and technical achievements
5. NEVER use negative language like "Unfortunately", "only has", "just", or "no stars"
6. Instead say: "Featured project", "Showcase project", "Demonstrates expertise in..."
7. Group similar projects when helpful
8. Be concise but informative
9. Respond in {context.language.value}
10. Format your response in a clear, professional manner

Provide a helpful, technical response that emphasizes the candidate's skills and project quality, not popularity metrics.
"""
        
        return prompt