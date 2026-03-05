"""
Guardrail Agent - Validates responses and handles out-of-scope requests.

New features:
- Web search fallback for CV-related queries with no DB info
- Smarter validation logic
"""

import logging
from typing import Optional

from backend.infrastructure.llm.provider import BaseLLMProvider
from backend.orchestrator.types import RequestContext, Intent, Language

logger = logging.getLogger(__name__)


def _get_language_name(lang: Language) -> str:
    """Convert language enum to readable name."""
    names = {
        Language.ENGLISH: "English",
        Language.TURKISH: "Turkish",
        Language.KURDISH: "Kurdish",
    }
    return names.get(lang, "English")


class GuardrailAgent:
    """
    Agent for validating responses and handling edge cases.
    
    Features:
    - Quick validation for obviously valid responses
    - LLM validation for suspicious responses
    - Web search fallback for "does not provide information"
    - Polite out-of-scope handling
    """
    
    def __init__(self, llm_provider: BaseLLMProvider):
        self.llm_provider = llm_provider
    
    async def check_response(
        self,
        response: str,
        context: RequestContext,
    ) -> str:
        """
        Check if response is appropriate and on-topic.
        
        Flow:
        1. Quick validation (keyword check)
        2. Detect "does not provide information" → Web search
        3. Suspicious patterns → LLM validation
        4. Otherwise → Pass through
        """
        if len(response) < 20:
            return response
        
        # Check for "no information" pattern → Web search
        if self._needs_web_search(response, context):
            logger.info("Response lacks info - triggering web search fallback")
            return await self._web_search_fallback(context)
        
        # Quick validation
        if self._is_clearly_valid(response, context):
            logger.debug("Response passed quick validation")
            return response
        
        # Suspicious → LLM validation
        if self._seems_suspicious(response):
            logger.info("Response flagged for LLM validation")
            return await self._validate_with_llm(response, context)
        
        return response
    
    def _needs_web_search(self, response: str, context: RequestContext) -> bool:
        """
        Detect if response says "no information available" for CV-related query.
        
        Triggers web search for:
        - Profile/skill questions
        - Technical terms (Redis, SEPA, etc.)
        """
        response_lower = response.lower()
        
        # Detect "no info" patterns
        no_info_patterns = [
            "does not provide",
            "does not include",
            "do not have",
            "no information",
            "bilgi bulunmamaktadır",
            "bilgi içermiyor",
            "bilgi yok",
        ]
        
        has_no_info = any(pattern in response_lower for pattern in no_info_patterns)
        
        if not has_no_info:
            return False
        
        # Only web search for CV-related queries (not out-of-scope)
        if context.intent in [Intent.PROFILE_INFO, Intent.GITHUB_INFO]:
            logger.info(f"No DB info for CV-related query: '{context.user_query}'")
            return True
        
        return False
    
    async def _web_search_fallback(self, context: RequestContext) -> str:
        """
        Perform web search when DB has no information.
        
        Use case: "Redis nedir?", "SEPA nedir?" gibi sorular
        """
        lang_name = _get_language_name(context.language)
        
        # Simple LLM call with instruction to search mentally
        # (Real web search would require web_search tool integration)
        
        search_prompt = f"""You are a helpful assistant. The user asked a technical question but the database doesn't have information about it.

USER QUESTION: {context.user_query}
RESPOND IN: {lang_name}

TASK: Provide a brief, accurate answer to this technical/CV-related question based on your knowledge.

Guidelines:
- Keep it concise (2-3 sentences)
- Focus on practical, relevant information
- If it's a technical term, explain it simply
- If it's about experience/skills, provide context
- Be helpful and informative

Your response:"""
        
        try:
            response = await self.llm_provider.generate(
                prompt=search_prompt,
                temperature=0.5,
                max_tokens=200,
            )
            
            logger.info("Web search fallback completed")
            return response.strip()
        
        except Exception as e:
            logger.error(f"Web search fallback failed: {e}")
            # Fallback to generic response
            if context.language == Language.TURKISH:
                return "Üzgünüm, bu bilgi şu anda mevcut değil."
            else:
                return "I'm sorry, this information is not currently available."
    
    def _is_clearly_valid(self, response: str, context: RequestContext) -> bool:
        """Quick validation for obviously valid responses."""
        response_lower = response.lower()
        
        # Check for relevant keywords based on intent
        if context.intent == Intent.PROFILE_INFO:
            valid_keywords = [
                "skill", "experience", "technology", "project",
                "yetenek", "deneyim", "teknoloji", "proje",
                "python", "javascript", "react", "backend"
            ]
            if any(kw in response_lower for kw in valid_keywords):
                return True
        
        elif context.intent == Intent.GITHUB_INFO:
            valid_keywords = ["repository", "repo", "github", "project", "code"]
            if any(kw in response_lower for kw in valid_keywords):
                return True
        
        # Long responses are probably valid
        if len(response) > 100:
            return True
        
        return False
    
    def _seems_suspicious(self, response: str) -> bool:
        """Check if response seems suspicious."""
        response_lower = response.lower()
        
        suspicious_patterns = [
            "i cannot", "i can't", "i'm not able",
            "out of scope", "not allowed",
            "yapamazım", "kapsam dışı",
        ]
        
        suspicious_count = sum(1 for p in suspicious_patterns if p in response_lower)
        return suspicious_count >= 2
    
    async def _validate_with_llm(self, response: str, context: RequestContext) -> str:
        """Use LLM to validate suspicious response."""
        validation_prompt = f"""Validate this response.

USER QUESTION: {context.user_query}
AGENT RESPONSE: {response}

Is this response appropriate and helpful?

Respond ONLY with:
- "APPROVE" if good
- "REJECT: [reason]" if bad

Your response:"""
        
        try:
            validation = await self.llm_provider.generate(
                prompt=validation_prompt,
                temperature=0.3,
                max_tokens=50,
            )
            
            if validation.strip().startswith("APPROVE"):
                logger.info("Response approved by guardrail")
                return response
            else:
                logger.warning(f"Response rejected: {validation}")
                return await self.handle_out_of_scope(context)
        
        except Exception as e:
            logger.error(f"Guardrail validation error: {e}")
            return response
    
    async def handle_out_of_scope(self, context: RequestContext) -> str:
        """Handle out-of-scope requests politely."""
        if context.language == Language.TURKISH:
            return "Üzgünüm, bu soru kapsam dışında. Adayın yetenekleri, deneyimi veya projeleri hakkında soru sorabilirsiniz."
        elif context.language == Language.KURDISH:
            return "Bibore, ev pirs di derveyî kar e. Tu dikarî li ser jêhatî, ezmûn an projeyên namzedî bipirsî."
        else:
            return "I'm sorry, this question is out of scope. You can ask about the candidate's skills, experience, or projects."