# ============================================================
# app/filters.py
# Output filtering and PII detection
# ============================================================

import re
from dataclasses import dataclass


@dataclass
class FilterResult:
    is_safe: bool
    issue_detected: str | None
    filtered_output: str
    redactions_made: list[str]
    confidence: float


class OutputFilter:
    """
    Multi-layer output filter applied to LLM responses.

    Runs AFTER the LLM generates — catches anything that slipped through.
    """

    # PII detection patterns
    PII_PATTERNS = {
        "email": (r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b', "[EMAIL_REDACTED]"),
        "phone_us": (r'\b(?:\+1[-.\s]?)?\(?\d{3}\)?[-.\s]?\d{3}[-.\s]?\d{4}\b', "[PHONE_REDACTED]"),
        "credit_card": (r'\b\d{4}[\s\-]?\d{4}[\s\-]?\d{4}[\s\-]?\d{4}\b', "[CC_REDACTED]"),
        "ssn": (r'\b\d{3}-\d{2}-\d{4}\b', "[SSN_REDACTED]"),
        "api_key_sk": (r'\bsk-[A-Za-z0-9]{20,}\b', "[API_KEY_REDACTED]"),
        "aws_key": (r'\bAKIA[0-9A-Z]{16}\b', "[AWS_KEY_REDACTED]"),
    }

    # System prompt leakage indicators
    SYSTEM_LEAK_PATTERNS = [
        r"(?i)(my|the)\s+(system\s+)?prompt\s+(says?|is|states?)",
        r"(?i)i\s+(am\s+)?(instructed|configured|trained)\s+to",
        r"(?i)(following|these)\s+are\s+my\s+instructions?",
        r"(?i)system:\s+you\s+(are|must|should)",
    ]

    # Hallucination confidence markers (detect low-confidence outputs)
    HALLUCINATION_MARKERS = [
        r"(?i)i('m| am)\s+(not\s+sure|unsure|uncertain)\s+but",
        r"(?i)i\s+(think|believe|assume)\s+(?:it might|it could|it may)",
        r"(?i)this\s+is\s+my\s+(best\s+)?guess",
        r"(?i)i\s+don'?t\s+have\s+(access\s+to|information\s+about)\s+real.?time",
    ]

    def filter(
        self,
        output: str,
        redact_pii: bool = True,
        check_system_leak: bool = True,
        check_length: bool = True,
        max_output_length: int = 10000
    ) -> FilterResult:
        """
        Filter LLM output for safety and compliance.

        Args:
            output: Raw LLM response text
            redact_pii: Whether to redact personal information
            check_system_leak: Whether to check for system prompt exposure
            check_length: Whether to enforce output length limits

        Returns:
            FilterResult with filtered output
        """
        filtered = output
        redactions = []

        # 1. PII Redaction
        if redact_pii:
            for pii_type, (pattern, replacement) in self.PII_PATTERNS.items():
                matches = re.findall(pattern, filtered)
                if matches:
                    filtered = re.sub(pattern, replacement, filtered)
                    redactions.append(pii_type)

            if redactions:
                return FilterResult(
                    is_safe=False,
                    issue_detected=f"pii_detected:{','.join(redactions)}",
                    filtered_output=filtered,
                    redactions_made=redactions,
                    confidence=0.95
                )

        # 2. System prompt leakage
        if check_system_leak:
            for pattern in self.SYSTEM_LEAK_PATTERNS:
                if re.search(pattern, filtered):
                    return FilterResult(
                        is_safe=False,
                        issue_detected="system_prompt_leak",
                        filtered_output="I can't share configuration details.",
                        redactions_made=[],
                        confidence=0.85
                    )

        # 3. Length limit
        if check_length and len(filtered) > max_output_length:
            truncated = filtered[:max_output_length]
            # Find last complete sentence
            last_period = truncated.rfind(".")
            if last_period > max_output_length * 0.8:
                truncated = truncated[:last_period + 1]
            truncated += "\n\n[Response truncated]"
            return FilterResult(
                is_safe=False,
                issue_detected="output_too_long",
                filtered_output=truncated,
                redactions_made=[],
                confidence=1.0
            )

        return FilterResult(
            is_safe=True,
            issue_detected=None,
            filtered_output=filtered,
            redactions_made=[],
            confidence=1.0
        )

    def check_hallucination_risk(self, output: str) -> dict:
        """
        Flag outputs that contain uncertainty markers.
        These might indicate hallucination risk.
        """
        markers_found = []
        for pattern in self.HALLUCINATION_MARKERS:
            if re.search(pattern, output):
                markers_found.append(pattern)

        return {
            "hallucination_risk": "high" if len(markers_found) >= 2 else "low" if not markers_found else "medium",
            "markers_found": len(markers_found),
            "note": "Consider adding a disclaimer if risk is high"
        }