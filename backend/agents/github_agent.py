
"""
GitHub Agent implementation.

Handles questions about GitHub repositories, projects, and tech stack.
Uses github_tools and optional semantic search to retrieve data.
"""

import logging
from typing import Optional, List

from sqlalchemy.orm import Session

from infrastructure.llm.provider import BaseLLMProvider
from orchestrator.types import RequestContext
from data_access.vector_db.retrieval import RAGRetrievalPipeline
from data_access.vector_db.vector_store import SourceType
from agents.prompts import (
    GITHUB_AGENT_SYSTEM_PROMPT,
    GITHUB_AGENT_INSTRUCTIONS,
    get_language_instruction,
)
from tools import github_tools
from tools import semantic_search_tools

logger = logging.getLogger(__name__)


class GitHubAgent:
    """
    Agent for handling GitHub-related queries.
    """

    def __init__(
        self,
        llm_provider: BaseLLMProvider,
        db_session: Optional[Session] = None,
        retrieval_pipeline: Optional[RAGRetrievalPipeline] = None,
    ):
        self.llm_provider = llm_provider
        self.db_session = db_session
        self.retrieval_pipeline = retrieval_pipeline

    async def process(self, context: RequestContext) -> str:
        if self.db_session is None:
            return "GitHub data is not available."

        github_data = await self._gather_github_data(context)
        prompt = self._build_prompt(context, github_data)

        return await self.llm_provider.generate(prompt)

    async def _gather_github_data(self, context: RequestContext) -> dict:
        return {
            "username": await github_tools.get_profile_github_username(
                profile_id=context.profile_id,
                db_session=self.db_session,
            ),
            "repositories": await github_tools.get_github_repositories(
                profile_id=context.profile_id,
                db_session=self.db_session,
            ),
        }

    def _build_prompt(
        self,
        context: RequestContext,
        github_data: dict,
    ) -> str:
        return "\n".join(
            [
                GITHUB_AGENT_SYSTEM_PROMPT,
                GITHUB_AGENT_INSTRUCTIONS,
                get_language_instruction(context.language),
                f"User Query: {context.user_query}",
                f"GitHub Data: {github_data}",
            ]
        )