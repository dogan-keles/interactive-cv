"""
Guardrail Agent implementation.

Enforces system boundaries and handles out-of-scope requests.
Uses LLM only, no tools or database access.
"""

import logging

from backend.infrastructure.llm.provider import BaseLLMProvider
from backend.orchestrator.types import RequestContext
from backend.agents.prompts import (
    GUARDRAIL_AGENT_SYSTEM_PROMPT,
    GUARDRAIL_AGENT_INSTRUCTIONS,
    get_language_instruction,
)

logger = logging.getLogger(__name__)


class GuardrailAgent:
    """
    Agent for enforcing system boundaries and handling out-of-scope requests.
    
    Validates responses and handles requests that fall outside system scope.
    Uses LLM only, no tools or database access.
    """
    
    def __init__(self, llm_provider: BaseLLMProvider):
        """
        Initialize GuardrailAgent.
        
        Args:
            llm_provider: LLM provider for generating responses
        """
        self.llm_provider = llm_provider
    
    async def check_response(
        self,
        response: str,
        context: RequestContext,
    ) -> str:
        """
        Check and validate an agent response.
        
        Ensures response is safe, appropriate, and within system boundaries.
        If response is invalid, returns a corrected version.
        
        Args:
            response: Agent-generated response to validate
            context: Request context
            
        Returns:
            Validated or corrected response
        """
        try:
            prompt = self._build_check_prompt(response, context)
            
            validated_response = await self.llm_provider.generate(
                prompt=prompt,
                temperature=0.3,
                max_tokens=200,
            )
            
            return validated_response.strip()
        
        except Exception as e:
            logger.error(f"GuardrailAgent check_response error: {e}", exc_info=True)
            return response
    
    async def handle_out_of_scope(
        self,
        context: RequestContext,
    ) -> str:
        """
        Handle out-of-scope or unsupported requests.
        
        Generates a polite refusal or redirection message.
        
        Args:
            context: Request context with user query
            
        Returns:
            Polite refusal or redirection message
        """
        try:
            prompt = self._build_out_of_scope_prompt(context)
            
            response = await self.llm_provider.generate(
                prompt=prompt,
                temperature=0.5,
                max_tokens=150,
            )
            
            return response.strip()
        
        except Exception as e:
            logger.error(f"GuardrailAgent handle_out_of_scope error: {e}", exc_info=True)
            if context.language.value == "tr":
                return "Üzgünüm, bu isteği yerine getiremiyorum. Lütfen adayın profesyonel geçmişi, GitHub projeleri veya CV oluşturma hakkında sorun."
            return "I'm sorry, I cannot fulfill this request. Please ask about the candidate's professional background, GitHub projects, or CV generation."
    
    def _build_check_prompt(
        self,
        response: str,
        context: RequestContext,
    ) -> str:
        """Build prompt for response validation."""
        prompt_parts = [
            GUARDRAIL_AGENT_SYSTEM_PROMPT,
            "",
            "Validate the following agent response. If it is safe, appropriate, and within system boundaries, return it as-is. If it violates boundaries, contains unsafe content, or goes off-topic, return a corrected version (max 4 sentences).",
            "",
            get_language_instruction(context.language),
            "",
            f"Original User Query: {context.user_query}",
            f"Agent Response to Validate: {response}",
            "",
            "Return the validated or corrected response:",
        ]
        return "\n".join(prompt_parts)
    
    def _build_out_of_scope_prompt(
        self,
        context: RequestContext,
    ) -> str:
        """Build prompt for out-of-scope request handling."""
        prompt_parts = [
            GUARDRAIL_AGENT_SYSTEM_PROMPT,
            "",
            GUARDRAIL_AGENT_INSTRUCTIONS,
            "",
            get_language_instruction(context.language),
            "",
            f"User Query: {context.user_query}",
            "",
            "Generate a response following the instructions above (max 4 sentences):",
        ]
        return "\n".join(prompt_parts)



