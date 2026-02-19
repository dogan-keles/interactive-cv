"""
AI Orchestrator - Central routing component.
"""

from typing import Optional, Protocol

from .intent_detector import detect_intent
from .language_detector import detect_language
from .types import Intent, Language, RequestContext


class Agent(Protocol):
    """Protocol for agent interface."""

    async def process(self, context: RequestContext) -> str:
        ...


class GuardrailAgentProtocol(Protocol):
    """Protocol for guardrail agent interface."""
    
    async def check_response(
        self,
        response: str,
        context: RequestContext,
    ) -> str:
        ...
    
    async def handle_out_of_scope(self, context: RequestContext) -> str:
        ...


class Orchestrator:
    """Central orchestrator for request routing."""

    def __init__(
        self,
        profile_agent: Optional[Agent] = None,
        github_agent: Optional[Agent] = None,
        cv_agent: Optional[Agent] = None,
        guardrail_agent: Optional[GuardrailAgentProtocol] = None,
    ):
        if guardrail_agent is None:
            raise ValueError("guardrail_agent must be provided")

        self.profile_agent = profile_agent
        self.github_agent = github_agent
        self.cv_agent = cv_agent
        self.guardrail_agent = guardrail_agent

    async def process_request(
        self,
        user_query: str,
        profile_id: int,
    ) -> str:
        """Process user request end-to-end."""
        language = detect_language(user_query)
        intent = detect_intent(user_query, language)
        
        context = RequestContext(
            user_query=user_query,
            profile_id=profile_id,
            language=language,
            intent=intent,
        )
        
        response = await self._route_to_agent(context)
        
        final_response = await self.guardrail_agent.check_response(
            response=response,
            context=context,
        )
        
        return final_response
    
    async def _route_to_agent(self, context: RequestContext) -> str:
        """Route request to appropriate agent based on intent."""
        if context.intent == Intent.PROFILE_INFO:
            return await self.profile_agent.process(context)
        
        elif context.intent == Intent.GITHUB_INFO:
            return await self.github_agent.process(context)
        
        elif context.intent == Intent.CV_REQUEST:
            return await self.cv_agent.process(context)
        
        elif context.intent == Intent.GENERAL_QUESTION:
            return await self.profile_agent.process(context)
        
        elif context.intent == Intent.OUT_OF_SCOPE:
            return await self.guardrail_agent.handle_out_of_scope(context)
        
        else:
            return await self.guardrail_agent.handle_out_of_scope(context)
    
    async def process_with_rag_context(
        self,
        user_query: str,
        profile_id: int,
        rag_context: Optional[str] = None,
    ) -> str:
        """Process request with pre-retrieved RAG context."""
        language = detect_language(user_query)
        intent = detect_intent(user_query, language)
        
        context = RequestContext(
            user_query=user_query,
            profile_id=profile_id,
            language=language,
            intent=intent,
            rag_context=rag_context,
        )
        
        response = await self._route_to_agent(context)
        
        final_response = await self.guardrail_agent.check_response(
            response=response,
            context=context,
        )
        
        return final_response