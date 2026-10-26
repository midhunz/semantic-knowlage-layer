"""Arabic/English helpers: search normalisation and language selection for agent output."""

import re

_TASHKEEL_TATWEEL = re.compile("[ً-ٰٟـ]")
_LETTERS = str.maketrans({"أ": "ا", "إ": "ا", "آ": "ا", "ٱ": "ا", "ى": "ي", "ئ": "ي", "ؤ": "و", "ة": "ه"})
_DIGITS = str.maketrans("٠١٢٣٤٥٦٧٨٩۰۱۲۳۴۵۶۷۸۹", "01234567890123456789")


def norm(text: str | None) -> str:
    """Fold case, Arabic diacritics/tatweel, alef/ya/ta-marbuta variants and Arabic-Indic digits."""
    if not text:
        return ""
    return _TASHKEEL_TATWEEL.sub("", text).translate(_LETTERS).translate(_DIGITS).lower().strip()


def hit(needle: str, *haystacks) -> bool:
    """True if the normalised needle occurs in any string (or string in a list) of haystacks."""
    n = norm(needle)
    if not n:
        return True
    for h in haystacks:
        for item in (h if isinstance(h, (list, tuple)) else [h]):
            if n in norm(str(item) if item is not None else ""):
                return True
    return False


def put(doc: dict, key: str, en, ar, lang: str) -> None:
    """Write a bilingual value into an agent-facing doc.

    lang="en": English only. "ar": Arabic, falling back to English. "both": `key` and `key_ar`.
    """
    if lang == "ar":
        value = ar or en
        if value:
            doc[key] = value
    elif lang == "both":
        if en:
            doc[key] = en
        if ar:
            doc[f"{key}_ar"] = ar
    elif en:
        doc[key] = en


def check_lang(lang: str) -> str:
    return lang if lang in ("en", "ar", "both") else "en"
