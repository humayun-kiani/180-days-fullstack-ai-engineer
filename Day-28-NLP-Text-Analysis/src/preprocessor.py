# ============================================================
# src/preprocessor.py
# Text preprocessing and cleaning utilities
# ============================================================

import re
import string
from typing import Optional

try:
    from nltk.corpus import stopwords
    from nltk.stem import PorterStemmer, WordNetLemmatizer
    NLTK_AVAILABLE = True
    STOP_WORDS = set(stopwords.words('english'))
    LEMMATIZER = WordNetLemmatizer()
    STEMMER = PorterStemmer()
except ImportError:
    NLTK_AVAILABLE = False
    STOP_WORDS = set()

# ─── Technical Vocabulary (don't remove these!) ─────────────

TECH_TERMS = {
    "api", "url", "http", "https", "sql", "null", "404", "500",
    "bug", "error", "crash", "fix", "patch", "deploy", "auth",
    "db", "ssl", "cdn", "cli", "sdk", "jwt", "oauth", "rest",
    "json", "xml", "html", "css", "js", "py", "python",
    "git", "pr", "ci", "cd", "docker", "redis", "nginx"
}

# Keep these stopwords if they change meaning
IMPORTANT_NEGATIONS = {"not", "no", "never", "without", "cannot", "can't",
                       "won't", "doesn't", "don't", "isn't", "aren't"}


def clean_text(text: str) -> str:
    """
    Basic text cleaning — normalize and remove noise.

    Args:
        text: Raw input text.

    Returns:
        str: Cleaned text string.
    """
    if not text or not isinstance(text, str):
        return ""

    # Lowercase
    text = text.lower()

    # Replace common contractions
    contractions = {
        "can't": "cannot", "won't": "will not", "n't": " not",
        "i'm": "i am", "it's": "it is", "they're": "they are",
        "we're": "we are", "doesn't": "does not", "don't": "do not",
        "didn't": "did not", "isn't": "is not", "aren't": "are not"
    }
    for contraction, expansion in contractions.items():
        text = text.replace(contraction, expansion)

    # Remove URLs
    text = re.sub(r'https?://\S+|www\.\S+', ' URL ', text)

    # Preserve error codes (HTTP 500, Error 404)
    text = re.sub(r'\b(http\s*\d{3})\b', lambda m: m.group().replace(' ', '_'), text)

    # Remove code blocks
    text = re.sub(r'```[\s\S]*?```', ' CODE_BLOCK ', text)
    text = re.sub(r'`[^`]+`', ' CODE ', text)

    # Remove HTML tags
    text = re.sub(r'<[^>]+>', ' ', text)

    # Remove special characters but keep apostrophes and hyphens in words
    text = re.sub(r'[^a-zA-Z0-9\s\-_]', ' ', text)

    # Normalize whitespace
    text = re.sub(r'\s+', ' ', text).strip()

    return text


def tokenize(text: str, use_lemmatization: bool = True) -> list[str]:
    """
    Tokenize and normalize text into meaningful tokens.

    Args:
        text: Cleaned text string.
        use_lemmatization: Apply lemmatization if NLTK available.

    Returns:
        list[str]: List of processed tokens.
    """
    # Split on whitespace and hyphens
    tokens = re.split(r'[\s\-_]+', text.lower())

    # Filter empty and very short tokens
    tokens = [t for t in tokens if len(t) > 1]

    # Remove pure numbers (keep alphanumeric like "http_500")
    tokens = [t for t in tokens if not t.isdigit() or t in TECH_TERMS]

    # Remove stopwords but preserve negations and tech terms
    if NLTK_AVAILABLE:
        filtered = []
        for token in tokens:
            if token in TECH_TERMS:
                filtered.append(token)    # always keep tech terms
            elif token in IMPORTANT_NEGATIONS:
                filtered.append(token)    # keep negations
            elif token in STOP_WORDS:
                continue                  # remove other stopwords
            elif len(token) > 2:
                filtered.append(token)
        tokens = filtered

    # Lemmatize
    if NLTK_AVAILABLE and use_lemmatization:
        tokens = [LEMMATIZER.lemmatize(t) for t in tokens]

    return tokens


def preprocess_for_model(text: str) -> str:
    """
    Full preprocessing pipeline that returns a string.
    Used for TF-IDF vectorization.

    Args:
        text: Raw input text.

    Returns:
        str: Preprocessed text string for vectorizer input.
    """
    cleaned = clean_text(text)
    tokens = tokenize(cleaned)
    return " ".join(tokens)


def preprocess_batch(texts: list[str]) -> list[str]:
    """Preprocess a list of texts."""
    return [preprocess_for_model(t) for t in texts]


def get_text_stats(text: str) -> dict:
    """Get basic statistics about a text."""
    words = text.split()
    sentences = re.split(r'[.!?]+', text)

    return {
        "char_count": len(text),
        "word_count": len(words),
        "sentence_count": len([s for s in sentences if s.strip()]),
        "avg_word_length": sum(len(w) for w in words) / len(words) if words else 0,
        "exclamation_count": text.count("!"),
        "question_count": text.count("?"),
        "uppercase_ratio": sum(1 for c in text if c.isupper()) / len(text) if text else 0,
        "has_code": bool(re.search(r'```|`[^`]+`', text)),
        "has_url": bool(re.search(r'https?://', text))
    }