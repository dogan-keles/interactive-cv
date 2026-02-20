"""
Language Detection - Majority-vote approach.

Counts known words in each language. The language with the most matches wins.
Defaults to Turkish if tied or uncertain.
"""

from .types import Language


# Common English words that appear in questions
ENGLISH_WORDS = {
    "what", "which", "who", "where", "when", "how", "why",
    "does", "did", "do", "is", "are", "was", "were", "has", "have", "had",
    "can", "could", "will", "would", "should",
    "the", "a", "an", "this", "that", "these", "those",
    "about", "with", "from", "for", "and", "but", "or", "not",
    "tell", "show", "give", "explain", "describe", "list",
    "me", "his", "her", "him", "their", "your", "my",
    "skills", "skill", "experience", "education", "background",
    "projects", "project", "work", "job", "career",
    "technology", "technologies", "programming", "languages",
    "contact", "email", "information", "info",
    "know", "like", "think", "want", "need",
    "please", "thanks", "hello", "hi", "hey",
    "good", "best", "most", "many", "much", "some", "any",
    "also", "very", "really", "just", "only",
    "years", "year", "company", "role", "position",
    "download", "resume", "summary", "profile",
}

# Turkish words (excluding names like Doğan)
TURKISH_WORDS = {
    "merhaba", "nedir", "neler", "nelerdir", "hangi", "nasıl", "neden", "nerede",
    "hakkında", "biliyor", "bilir", "sahip", "yapıyor", "çalışıyor",
    "yetenekleri", "yetenek", "beceri", "becerileri", "deneyim", "deneyimi",
    "tecrübe", "teknoloji", "teknolojileri", "proje", "projeleri",
    "özgeçmiş", "indir", "göster", "anlat", "açıkla", "listele",
    "kimdir", "kim", "kimin", "ne", "neyi",
    "çalışmış", "eğitim", "üniversite", "okul",
    "şirket", "pozisyon", "kariyer", "geçmiş", "uzmanlık",
    "iletişim", "ulaş", "ulaşabilirim",
    "bana", "söyle", "söyler", "misin", "mısın", "misiniz",
    "bir", "bu", "şu", "ve", "ile", "için", "var", "mı", "mi", "mu", "mü",
    "en", "çok", "fazla", "kaç", "tane",
    "lütfen", "teşekkürler", "selam",
    "evet", "hayır", "tamam",
}

# Kurdish words
KURDISH_WORDS = {
    "çi", "dizane", "teknolojî", "namzed", "jêhatî", "ezmûn",
    "zanîn", "pispor", "çawa", "kengê", "li", "ku", "bibore",
    "dikarî", "projeyên", "derbarê", "navnîşan", "bersiv",
    "nikare", "hene", "heye", "tune", "baş",
    "ez", "tu", "ew", "em", "hûn", "wan",
    "bi", "ji", "di", "de", "re", "ra",
    "kar", "xebat",
}

# German words
GERMAN_WORDS = {
    "was", "welche", "wer", "wo", "wann", "wie", "warum",
    "kenntnisse", "erfahrung", "fähigkeiten", "ausbildung",
    "lebenslauf", "projekt", "projekte", "arbeit",
    "können", "über", "zeig", "erzähl",
    "ist", "sind", "hat", "haben",
    "der", "die", "das", "ein", "eine",
    "und", "oder", "aber", "nicht",
    "bitte", "danke", "hallo",
}

# French words
FRENCH_WORDS = {
    "quelles", "quel", "qui", "quoi", "comment", "pourquoi",
    "compétences", "expérience", "projets", "formation",
    "montrez", "parlez", "candidat", "travail",
    "est", "sont", "les", "des", "une", "avec",
    "bonjour", "merci", "oui", "non",
}

# Spanish words
SPANISH_WORDS = {
    "cuáles", "qué", "quién", "cómo", "dónde", "por",
    "habilidades", "experiencia", "proyectos", "educación",
    "muestra", "candidato", "trabajo", "conocimientos",
    "tiene", "puede", "sabe",
    "hola", "gracias",
}


def _count_matches(text_words: set, language_words: set) -> int:
    """Count how many words from text match a language's word set."""
    return len(text_words & language_words)


def detect_language(text: str) -> Language:
    """
    Detect language by counting word matches across languages.

    The language with the most matching words wins.
    Defaults to Turkish if tied or no matches.
    """
    if not text or not text.strip():
        return Language.TURKISH

    # Tokenize: lowercase, split, expand contractions/punctuation
    text_lower = text.lower()
    words = set(text_lower.split())
    expanded_words = set()
    for word in words:
        expanded_words.add(word)
        for part in word.replace("'", " ").replace("\u2019", " ").replace(",", " ").replace(".", " ").replace("?", "").replace("!", "").split():
            if part:
                expanded_words.add(part)

    scores = {
        Language.ENGLISH: _count_matches(expanded_words, ENGLISH_WORDS),
        Language.TURKISH: _count_matches(expanded_words, TURKISH_WORDS),
        Language.KURDISH: _count_matches(expanded_words, KURDISH_WORDS),
        Language.GERMAN: _count_matches(expanded_words, GERMAN_WORDS),
        Language.FRENCH: _count_matches(expanded_words, FRENCH_WORDS),
        Language.SPANISH: _count_matches(expanded_words, SPANISH_WORDS),
    }

    # Find the language with the highest score
    best_lang = Language.TURKISH
    best_score = 0

    for lang, score in scores.items():
        if score > best_score:
            best_score = score
            best_lang = lang

    # If no matches at all, default to Turkish
    if best_score == 0:
        return Language.TURKISH

    return best_lang


def get_language_name(lang: Language) -> str:
    """Get human-readable language name."""
    names = {
        Language.AUTO: "Turkish",
        Language.ENGLISH: "English",
        Language.TURKISH: "Turkish",
        Language.KURDISH: "Kurdish (Kurmancî)",
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
    return names.get(lang, "Turkish")


# Legacy compatibility
class LanguageDetector:
    def detect(self, text: str) -> Language:
        return detect_language(text)

    def detect_with_confidence(self, text: str) -> tuple[Language, float]:
        return detect_language(text), 1.0


_language_detector = LanguageDetector()