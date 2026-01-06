"""
Language detection for user input.

Lightweight, deterministic language detection executed before intent classification.
Uses character-based heuristics for Turkish/English detection.
"""

import re
from typing import Optional

from .types import Language


class LanguageDetector:
    """
    Detects language of user input using character-based heuristics.
    
    Turkish-specific characters: ç, ğ, ı, ö, ş, ü, Ç, Ğ, İ, Ö, Ş, Ü
    English is the default fallback.
    """
    
    # Turkish-specific characters (lowercase and uppercase)
    TURKISH_CHARS = set("çğıöşüÇĞİÖŞÜ")
    
    # Common Turkish words (case-insensitive)
    TURKISH_KEYWORDS = {
        "ve", "ile", "için", "bu", "şu", "o", "bir", "var", "yok",
        "nedir", "nasıl", "ne", "kim", "nerede", "ne zaman",
        "hakkında", "ile ilgili", "projeler", "deneyim", "beceriler",
        "cv", "özgeçmiş", "github", "proje", "teknoloji",
    }
    
    def detect(self, text: str) -> Language:
        """
        Detect language of input text.
        
        Strategy:
        1. Check for Turkish-specific characters
        2. Check for common Turkish keywords
        3. Default to English
        
        Args:
            text: User input text
            
        Returns:
            Detected language (Language enum)
        """
        if not text or not text.strip():
            return Language.ENGLISH
        
        text_lower = text.lower()
        
        # Check for Turkish characters
        has_turkish_chars = any(char in self.TURKISH_CHARS for char in text)
        
        # Check for Turkish keywords
        turkish_keyword_count = sum(
            1 for keyword in self.TURKISH_KEYWORDS
            if keyword in text_lower
        )
        
        # Heuristic: If Turkish chars present OR 2+ Turkish keywords, classify as Turkish
        if has_turkish_chars or turkish_keyword_count >= 2:
            return Language.TURKISH
        
        # Check for mixed content (Turkish chars but mostly English)
        # If text is mostly English words but has some Turkish chars, still Turkish
        if has_turkish_chars:
            return Language.TURKISH
        
        # Default to English
        return Language.ENGLISH
    
    def detect_with_confidence(
        self,
        text: str,
    ) -> tuple[Language, float]:
        """
        Detect language with confidence score (0.0 to 1.0).
        
        Returns:
            Tuple of (detected_language, confidence_score)
        """
        if not text or not text.strip():
            return Language.ENGLISH, 0.5
        
        text_lower = text.lower()
        
        # Count Turkish indicators
        turkish_char_count = sum(1 for char in text if char in self.TURKISH_CHARS)
        turkish_keyword_count = sum(
            1 for keyword in self.TURKISH_KEYWORDS
            if keyword in text_lower
        )
        
        # Calculate confidence
        total_chars = len(text)
        char_ratio = turkish_char_count / total_chars if total_chars > 0 else 0
        keyword_ratio = min(turkish_keyword_count / 5.0, 1.0)  # Cap at 1.0
        
        # Combined confidence for Turkish
        turkish_confidence = min((char_ratio * 0.7 + keyword_ratio * 0.3) * 2, 1.0)
        
        if turkish_confidence > 0.3:
            return Language.TURKISH, turkish_confidence
        
        english_confidence = 1.0 - turkish_confidence
        return Language.ENGLISH, english_confidence


# Singleton instance
_language_detector = LanguageDetector()


def detect_language(text: str) -> Language:
    """
    Convenience function for language detection.
    
    Args:
        text: User input text
        
    Returns:
        Detected language
    """
    return _language_detector.detect(text)




