"""
Guardrail Agent - Validates responses and handles out-of-scope requests.
"""

import logging
from typing import Optional

from backend.infrastructure.llm.provider import BaseLLMProvider
from backend.orchestrator.types import RequestContext, Intent, Language
from backend.agents.prompts import (
    GUARDRAIL_AGENT_SYSTEM_PROMPT,
    GUARDRAIL_AGENT_INSTRUCTIONS,
)

logger = logging.getLogger(__name__)


class GuardrailAgent:
    """Agent for validating responses and handling edge cases."""
    
    def __init__(self, llm_provider: BaseLLMProvider):
        self.llm_provider = llm_provider
    
    async def check_response(
        self,
        response: str,
        context: RequestContext,
    ) -> str:
        """Check if a response is appropriate and on-topic."""
        if len(response) < 20:
            return response
        
        if self._is_clearly_valid(response, context):
            logger.debug("Response passed quick validation")
            return response
        
        if self._seems_suspicious(response):
            logger.info("Response flagged for LLM validation")
            return await self._validate_with_llm(response, context)
        
        return response
    
    def _is_clearly_valid(self, response: str, context: RequestContext) -> bool:
        """Quick checks for obviously valid responses."""
        response_lower = response.lower()
        
        if context.intent == Intent.PROFILE_INFO:
            valid_keywords = [
                "skill", "experience", "technology", "project", "background",
                "yetenek", "deneyim", "teknoloji", "proje", "geçmiş",
                "jêhatî", "zanîn", "pispor", "kar",
                "python", "javascript", "fastapi", "react"
            ]
            if any(keyword in response_lower for keyword in valid_keywords):
                return True
        
        elif context.intent == Intent.GITHUB_INFO:
            valid_keywords = [
                "repository", "repo", "github", "project", "code",
                "depo", "proje", "kod"
            ]
            if any(keyword in response_lower for keyword in valid_keywords):
                return True
        
        elif context.intent == Intent.CV_REQUEST:
            valid_keywords = [
                "cv", "resume", "download", "generate",
                "özgeçmiş", "indir"
            ]
            if any(keyword in response_lower for keyword in valid_keywords):
                return True
        
        if len(response) > 100:
            return True
        
        return False
    
    def _seems_suspicious(self, response: str) -> bool:
        """Check if response seems suspicious and needs validation."""
        response_lower = response.lower()
        
        suspicious_patterns = [
            "i cannot", "i can't", "i'm not able", "i'm unable",
            "out of scope", "not allowed", "cannot help",
            "redirect", "contact", "speak with",
            "yapamazım", "yapamam", "iznim yok",
            "kapsam dışı", "yetkim yok",
            "nikare", "nasiheyê"
        ]
        
        suspicious_count = sum(1 for pattern in suspicious_patterns if pattern in response_lower)
        
        return suspicious_count >= 2
    
    async def _validate_with_llm(
        self,
        response: str,
        context: RequestContext,
    ) -> str:
        """Use LLM to validate response."""
        validation_prompt = f"""You are a guardrail validator. Check if this response is appropriate.

USER QUESTION: {context.user_query}
INTENT: {context.intent.value}

AGENT RESPONSE:
{response}

TASK: Is this response appropriate and on-topic?

Guidelines:
- If the response answers the question about profile/skills/experience → APPROVE
- If the response provides helpful CV-related information → APPROVE
- If the response is overly restrictive or refuses valid requests → REJECT
- If the response is completely off-topic → REJECT
- If the response hallucinates or makes things up → REJECT

Respond ONLY with:
- "APPROVE" if the response is good
- "REJECT: [brief reason]" if it should be blocked

Your response:"""
        
        try:
            validation = await self.llm_provider.generate(
                prompt=validation_prompt,
                temperature=0.3,
                max_tokens=100,
            )
            
            if validation.strip().startswith("APPROVE"):
                logger.info("Response approved by guardrail validation")
                return response
            else:
                logger.warning(f"Response rejected by guardrail: {validation}")
                return await self.handle_out_of_scope(context)
        
        except Exception as e:
            logger.error(f"Guardrail validation error: {e}")
            return response
    
    async def handle_out_of_scope(self, context: RequestContext) -> str:
        """Handle out-of-scope requests politely."""
        query = context.user_query.strip()
        if len(query) < 3 or (not any(c.isalpha() for c in query)):
            if context.language == Language.TURKISH:
                return "Üzgünüm, sorunuzu anlamadım. Adayın yetenekleri, deneyimi veya projeleri hakkında soru sorabilirsiniz."
            elif context.language == Language.KURDISH:
                return "Bibore, ez pirsê te fêm nekim. Tu dikarî li ser jêhatî, ezmûn an projeyên namzedî bipirsî."
            else:
                return "I'm sorry, I didn't understand your question. You can ask about the candidate's skills, experience, or projects."
        
        prompt = f"""{GUARDRAIL_AGENT_SYSTEM_PROMPT}

{GUARDRAIL_AGENT_INSTRUCTIONS}

USER QUESTION: {context.user_query}
DETECTED LANGUAGE: {context.language.value}

This request is out of scope. Provide a polite response that:
1. Explains this system only handles profile/CV/GitHub questions
2. Suggests what the user CAN ask about instead
3. Is brief (2-3 sentences max)
4. Is in the SAME language as the user's question

⚠️  CRITICAL: Respond in the SAME language as the user's question!

Your response:"""
        
        try:
            response = await self.llm_provider.generate(
                prompt=prompt,
                temperature=0.7,
                max_tokens=200,
            )
            return response.strip()
        
        except Exception as e:
            logger.error(f"GuardrailAgent error: {e}")
            if context.language == Language.TURKISH:
                return "Üzgünüm, bu soru kapsam dışında. Adayın yetenekleri, deneyimi veya projeleri hakkında soru sorabilirsiniz."
            elif context.language == Language.KURDISH:
                return "Bibore, ev pirs di derveyî kar e. Tu dikarî li ser jêhatî, ezmûn an jî projeyên namzedî bipirsî."
            else:
                return "I'm sorry, this question is out of scope. You can ask about the candidate's skills, experience, or projects."