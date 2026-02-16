import re


def detect_language_local(text: str) -> str | None:
    """Heuristic language detection for en/ru/uk/sk."""
    if not text:
        return None

    lowered = text.lower()
    
    # Check for Cyrillic
    if re.search(r"[\u0400-\u04ff]", lowered):
        # Ukrainian-specific characters (і, ї, є, ґ)
        has_uk_markers = any(ch in lowered for ch in ("\u0456", "\u0457", "\u0454", "\u0491"))
        if has_uk_markers:
            return "uk"
        
        # Russian-specific characters (ъ, ы, э, ё)
        has_ru_markers = any(ch in lowered for ch in ("\u044a", "\u044b", "\u044d", "\u0451"))
        if has_ru_markers:
            return "ru"
        
        # If has Cyrillic but neither uk nor ru specific chars
        # Default to Ukrainian (more common in this context for the app)
        return "uk"

    # Check for Slovak diacritics
    if re.search(
        r"[\u00e1\u00e4\u010d\u010f\u00e9\u00ed\u013a\u013e\u0148"
        r"\u00f3\u00f4\u0155\u0161\u0165\u00fa\u00fd\u017e]",
        lowered,
    ):
        return "sk"

    # Check for Latin letters
    if re.search(r"[a-z]", lowered):
        return "en"

    return None
