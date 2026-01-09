"""
LLM-based Language Detection.

The LLM automatically detects and responds in the user's language.
No more hardcoded keyword matching or character detection.

This approach:
- Supports ALL languages (English, Turkish, Kurdish, Arabic, Chinese, etc.)
- No maintenance needed for new languages
- More accurate (LLM understands context)
- Simpler codebase
"""

from .types import Language


def detect_language(text: str) -> Language:
    """
    Return AUTO mode - LLM will detect language dynamically.
    
    This function now simply returns Language.AUTO, indicating that
    the LLM should detect and match the user's language automatically.
    
    The old keyword/character-based detection has been removed in favor
    of letting the LLM handle this naturally through its prompt.
    
    Args:
        text: User input text (not analyzed anymore)
        
    Returns:
        Language.AUTO (signals LLM-based detection)
    """
    return Language.AUTO


def get_language_name(lang: Language) -> str:
    """
    Get human-readable language name.
    
    Args:
        lang: Language enum value
        
    Returns:
        Human-readable language name
    """
    names = {
        Language.AUTO: "Auto-detected",
        Language.ENGLISH: "English",
        Language.TURKISH: "Turkish",
        Language.KURDISH: "Kurdish",
        Language.GERMAN: "German",
        Language.FRENCH: "French",
        Language.SPANISH: "Spanish",
        Language.ITALIAN: "Italian",
        Language.PORTUGUESE: "Portuguese",
        Language.RUSSIAN: "Russian",
        Language.ARABIC: "Arabic",
        Language.CHINESE: "Chinese",
        Language.JAPANESE: "Japanese",
        Language.KOREAN: "Korean",
    }
    return names.get(lang, "Auto-detected")


# Legacy class kept for backwards compatibility
class LanguageDetector:
    """
    Legacy LanguageDetector class (deprecated).
    
    Kept for backwards compatibility. All methods now return Language.AUTO.
    """
    
    def detect(self, text: str) -> Language:
        """Return AUTO mode for LLM-based detection."""
        return Language.AUTO
    
    def detect_with_confidence(self, text: str) -> tuple[Language, float]:
        """Return AUTO mode with 100% confidence (LLM handles it)."""
        return Language.AUTO, 1.0


# Singleton instance (for backwards compatibility)
_language_detector = LanguageDetector()