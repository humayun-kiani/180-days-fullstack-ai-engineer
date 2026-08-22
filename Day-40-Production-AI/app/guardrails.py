# ============================================================
# app/guardrails.py
# Consolidated guardrail pipeline from Day 38
# ============================================================

import re
import html
from dataclasses import dataclass


@dataclass
class GuardrailResult:
    safe: bool
    threat: str | None
    action: str           # "pass", "block", "sanitize"
    risk_score: float
    safe_input: str | None


INJECTION_PATTERNS = [
    r"(?i)ignore\s+(all\s+)?previous\s+instructions?",
    r"(?i)forget\s+(all\s+)?instructions?",
    r"(?i)disregard\s+(all\s+)?instructions?",
    r"(?i)you\s+are\s+now\s+(DAN|GPT|unrestricted)",
    r"(?i)reveal\s+(your\s+)?system\s+prompt",
    r"(?i)print\s+(your\s+)?instructions?",
    r"(?i)act\s+as\s+(an?\s+AI\s+without|if\s+you\s+have\s+no)\s+restrict",
]

SQL_PATTERNS = [
    r"(?i)(drop|delete|truncate)\s+table",
    r"(?i)union\s+select",
    r"(?i);\s*(drop|delete|select|insert)",
    r"'[\s]*--",
]

PII_PATTERNS = {
    "email":       r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b',
    "phone":       r'\b(?:\+1[-.\s]?)?\(?\d{3}\)?[-.\s]?\d{3}[-.\s]?\d{4}\b',
    "credit_card": r'\b\d{4}[\s\-]?\d{4}[\s\-]?\d{4}[\s\-]?\d{4}\b',
    "api_key":     r'\b(sk-|sk_live_)[A-Za-z0-9]{20,}\b',
}

SYSTEM_LEAK_PATTERNS = [
    r"(?i)(my|the)\s+(system\s+)?prompt\s+(says?|is|states?)",
    r"(?i)i\s+(am\s+)?(instructed|configured)\s+to",
]


def validate_input(text: str, max_length: int = 5000) -> GuardrailResult:
    """Validate user input — runs before LLM call."""
    if len(text) > max_length:
        return GuardrailResult(False, "too_long", "block", 0.3, None)

    if not text.strip():
        return GuardrailResult(False, "empty", "block", 0.1, None)

    for pattern in INJECTION_PATTERNS:
        if re.search(pattern, text):
            return GuardrailResult(False, "prompt_injection", "block", 0.95, None)

    for pattern in SQL_PATTERNS:
        if re.search(pattern, text):
            return GuardrailResult(False, "sql_injection", "block", 0.9, None)

    if re.search(r"<script[^>]*>|javascript:", text, re.IGNORECASE):
        sanitized = html.escape(text)
        return GuardrailResult(False, "xss", "sanitize", 0.8, sanitized)

    words = text.split()
    if len(words) > 20:
        unique_ratio = len(set(words)) / len(words)
        if unique_ratio < 0.1:
            return GuardrailResult(False, "repetition_dos", "block", 0.5, None)

    return GuardrailResult(True, None, "pass", 0.0, text.strip())


def filter_output(text: str) -> tuple[str, list[str]]:
    """Filter LLM output — runs after LLM call. Returns (filtered, issues)."""
    filtered = text
    issues = []

    for pii_type, pattern in PII_PATTERNS.items():
        if re.search(pattern, filtered):
            filtered = re.sub(pattern, f"[{pii_type.upper()}_REDACTED]", filtered)
            issues.append(f"pii:{pii_type}")

    for pattern in SYSTEM_LEAK_PATTERNS:
        if re.search(pattern, filtered):
            return "I can't share configuration details.", ["system_leak"]

    if len(filtered) > 20000:
        filtered = filtered[:20000] + "\n\n[Response truncated]"
        issues.append("output_too_long")

    return filtered, issues