"""
AI Orchestrator - Central routing component.

Receives user messages, detects language and intent,
routes to appropriate agents, and aggregates responses.
"""

from typing import Optional, Protocol

from .intent_detector import detect_intent
from .language_detector import detect_language
from .types import Intent, Language, RequestContext


class Agent(Protocol):
    """Protocol for agent interface."""
    
    async def process(self, context: RequestContext) -> str:
        """Process request with context."""
        ...


class GuardrailAgentProtocol(Protocol):
    """Protocol for guardrail agent interface."""
    
    async def check_response(
        self,
        response: str,
        context: RequestContext,
    ) -> str:
        """Check and validate response."""
        ...
    
    async def handle_out_of_scope(self, context: RequestContext) -> str:
        """Handle out-of-scope requests."""
        ...


class Orchestrator:
    """
    Central orchestrator for request routing.
    
    Responsibilities:
    1. Language detection
    2. Intent detection
    3. Agent routing
    4. Response aggregation
    
    Does NOT:
    - Access databases directly
    - Generate content without agent input
    - Call LLM directly
    """
    
    def __init__(
        self,
        profile_agent: Optional[Agent] = None,
        github_agent: Optional[Agent] = None,
        cv_agent: Optional[Agent] = None,
        guardrail_agent: Optional[GuardrailAgentProtocol] = None,
    ):
        """
        Initialize orchestrator with agent instances.
        
        Args:
            profile_agent: Profile agent instance
            github_agent: GitHub agent instance
            cv_agent: CV agent instance
            guardrail_agent: Guardrail agent instance
        """
        # Agents will be injected at runtime
        # For now, raise error if not provided (agents must be implemented)
        if profile_agent is None:
            raise ValueError("profile_agent must be provided")
        if github_agent is None:
            raise ValueError("github_agent must be provided")
        if cv_agent is None:
            raise ValueError("cv_agent must be provided")
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
        """
        Process user request end-to-end.
        
        Flow:
        1. Detect language
        2. Detect intent
        3. Create request context
        4. Route to appropriate agent
        5. Return response (in detected language)
        
        Args:
            user_query: User's input text
            profile_id: Profile identifier
            
        Returns:
            Agent response (in detected language)
        """
        # Step 1: Language detection (executed first)
        language = detect_language(user_query)
        
        # Step 2: Intent detection (uses detected language)
        intent = detect_intent(user_query, language)
        
        # Step 3: Create request context
        context = RequestContext(
            user_query=user_query,
            profile_id=profile_id,
            language=language,
            intent=intent,
        )
        
        # Step 4: Route to appropriate agent
        response = await self._route_to_agent(context)
        
        # Step 5: Apply guardrail check (always, before returning)
        final_response = await self.guardrail_agent.check_response(
            response=response,
            context=context,
        )
        
        return final_response
    
    async def _route_to_agent(
        self,
        context: RequestContext,
    ) -> str:
        """
        Route request to appropriate agent based on intent.
        
        Args:
            context: Request context with intent and language
            
        Returns:
            Agent response
        """
        if context.intent == Intent.PROFILE_INFO:
            return await self.profile_agent.process(context)
        
        elif context.intent == Intent.GITHUB_INFO:
            return await self.github_agent.process(context)
        
        elif context.intent == Intent.CV_REQUEST:
            return await self.cv_agent.process(context)
        
        elif context.intent == Intent.GENERAL_QUESTION:
            # General questions can be handled by profile agent
            # or a dedicated general agent if needed
            return await self.profile_agent.process(context)
        
        elif context.intent == Intent.OUT_OF_SCOPE:
            return await self.guardrail_agent.handle_out_of_scope(context)
        
        else:
            # Fallback to guardrail agent
            return await self.guardrail_agent.handle_out_of_scope(context)
    
    async def process_with_rag_context(
        self,
        user_query: str,
        profile_id: int,
        rag_context: Optional[str] = None,
    ) -> str:
        """
        Process request with pre-retrieved RAG context.
        
        Useful when RAG context is retrieved before routing
        (e.g., by the API layer or orchestrator itself).
        
        Args:
            user_query: User's input text
            profile_id: Profile identifier
            rag_context: Pre-retrieved RAG context
            
        Returns:
            Agent response
        """
        # Detect language and intent
        language = detect_language(user_query)
        intent = detect_intent(user_query, language)
        
        # Create context with RAG
        context = RequestContext(
            user_query=user_query,
            profile_id=profile_id,
            language=language,
            intent=intent,
            rag_context=rag_context,
        )
        
        # Route to agent
        response = await self._route_to_agent(context)
        
        # Apply guardrail
        final_response = await self.guardrail_agent.check_response(
            response=response,
            context=context,
        )
        
        return final_response

