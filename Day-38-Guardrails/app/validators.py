# ============================================================
# app/validators.py
# Input validation and sanitization
# ============================================================

import re
import html
from dataclasses import dataclass


@dataclass
class ValidationResult:
    is_safe: bool
    threat_detected: str | None
    sanitized_input: str | None
    risk_score: float
    details: str = ""


class InputValidator:
    """
    Multi-layer input validator.

    Checks run in order of severity (fail-fast on critical threats).
    """

    MAX_LENGTH = 5000

    # Prompt injection — direct override attempts
    INJECTION_PATTERNS = [
        (r"(?i)ignore\s+(all\s+)?previous\s+instructions?",    "direct_override",  0.95),
        (r"(?i)forget\s+(all\s+)?previous\s+instructions?",    "direct_override",  0.95),
        (r"(?i)disregard\s+(all\s+)?instructions?",            "direct_override",  0.90),
        (r"(?i)you\s+are\s+now\s+(DAN|GPT-?4|unrestricted)",   "persona_override", 0.95),
        (r"(?i)act\s+as\s+(DAN|an?\s+AI\s+without\s+restrict)", "persona_override", 0.90),
        (r"(?i)pretend\s+you\s+(have\s+no|are\s+without)\s+restrict", "persona_override", 0.88),
        (r"(?i)reveal\s+(your\s+)?(system\s+)?prompt",         "exfiltration",    0.92),
        (r"(?i)print\s+(your\s+)?instructions?",               "exfiltration",    0.85),
        (r"(?i)what\s+(are\s+)?your\s+(full\s+)?instructions?","exfiltration",    0.80),
        (r"(?i)show\s+me\s+your\s+(system\s+)?prompt",        "exfiltration",    0.85),
    ]

    # SQL injection patterns
    SQL_PATTERNS = [
        (r"(?i)(drop|delete|truncate)\s+table",   "sql_ddl",       0.95),
        (r"(?i)union\s+select",                   "sql_union",     0.90),
        (r"(?i);\s*(drop|delete|select|insert)",  "sql_chain",     0.90),
        (r"(?i)insert\s+into\s+\w+\s*values",     "sql_insert",    0.85),
        (r"'[\s]*--",                             "sql_comment",   0.80),
        (r"(?i)1\s*=\s*1",                       "sql_tautology", 0.70),
    ]

    # Script injection
    SCRIPT_PATTERNS = [
        (r"<script[^>]*>",          "xss_script",  0.95),
        (r"javascript:",            "xss_proto",   0.85),
        (r"on\w+\s*=\s*['\"]",     "xss_event",   0.80),
    ]

    def validate(
        self,
        text: str,
        context: str = "general",
        max_length: int | None = None
    ) -> ValidationResult:
        max_len = max_length or self.MAX_LENGTH

        # 1. Length check
        if len(text) > max_len:
            truncated = text[:max_len]
            return ValidationResult(
                is_safe=False,
                threat_detected="input_too_long",
                sanitized_input=truncated,
                risk_score=0.3,
                details=f"Input length {len(text)} exceeds max {max_len}"
            )

        # 2. Empty / whitespace only
        if not text.strip():
            return ValidationResult(
                is_safe=False,
                threat_detected="empty_input",
                sanitized_input=None,
                risk_score=0.1,
                details="Input is empty or whitespace only"
            )

        # 3. Prompt injection (highest priority — check first)
        for pattern, threat_type, risk in self.INJECTION_PATTERNS:
            if re.search(pattern, text):
                return ValidationResult(
                    is_safe=False,
                    threat_detected=f"prompt_injection:{threat_type}",
                    sanitized_input=None,
                    risk_score=risk,
                    details=f"Prompt injection pattern detected: {threat_type}"
                )

        # 4. SQL injection (for task/database contexts)
        if context in ("task", "database", "general"):
            for pattern, threat_type, risk in self.SQL_PATTERNS:
                if re.search(pattern, text):
                    return ValidationResult(
                        is_safe=False,
                        threat_detected=f"sql_injection:{threat_type}",
                        sanitized_input=None,
                        risk_score=risk,
                        details=f"SQL injection pattern: {threat_type}"
                    )

        # 5. Script injection
        for pattern, threat_type, risk in self.SCRIPT_PATTERNS:
            if re.search(pattern, text, re.IGNORECASE):
                # Sanitize rather than block (HTML-encode)
                sanitized = html.escape(text)
                return ValidationResult(
                    is_safe=False,
                    threat_detected=f"script_injection:{threat_type}",
                    sanitized_input=sanitized,
                    risk_score=risk,
                    details=f"Script injection detected and HTML-encoded"
                )

        # 6. Excessive repetition (DoS attempt)
        words = text.split()
        if len(words) > 20:
            word_set = set(words)
            if len(word_set) < len(words) * 0.1:    # >90% repeated
                return ValidationResult(
                    is_safe=False,
                    threat_detected="repetition_dos",
                    sanitized_input=None,
                    risk_score=0.5,
                    details="Excessive repetition detected (potential DoS)"
                )

        # 7. All clear
        return ValidationResult(
            is_safe=True,
            threat_detected=None,
            sanitized_input=text.strip(),
            risk_score=0.0,
            details="All validation checks passed"
        )

    def sanitize(self, text: str) -> str:
        """
        Sanitize input without full validation.
        Useful for cleaning text that will go into database fields.
        """
        # Remove null bytes
        text = text.replace("\x00", "")
        # Normalize whitespace
        text = re.sub(r"\s+", " ", text).strip()
        # HTML-encode angle brackets
        text = text.replace("<", "&lt;").replace(">", "&gt;")
        return text