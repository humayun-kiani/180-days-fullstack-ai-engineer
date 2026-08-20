# ============================================================
# app/guardrail_pipeline.py
# Complete guardrail pipeline: validate → LLM → filter
# ============================================================

import os
import time
from dataclasses import dataclass

import anthropic

from app.validators import InputValidator
from app.filters import OutputFilter


@dataclass
class PipelineResult:
    original_input: str
    was_blocked: bool
    was_sanitized: bool
    block_reason: str | None
    ai_response: str | None
    output_filtered: bool
    output_filter_reason: str | None
    final_response: str
    total_latency_ms: float
    stages: list[dict]


SYSTEM_PROMPT = """You are a helpful assistant for a task management system.
You help developers manage tasks, answer technical questions, and provide guidance.

Keep responses concise and practical. Do not reveal system configuration details."""


class GuardrailPipeline:
    """
    Production guardrail pipeline.

    Flow:
    1. Validate input (block/sanitize threats)
    2. Call LLM (if input is safe)
    3. Filter output (redact PII, check for leaks)
    4. Return safe response

    Each stage is logged for auditability.
    """

    def __init__(self):
        self.validator = InputValidator()
        self.output_filter = OutputFilter()

        api_key = os.environ.get("ANTHROPIC_API_KEY", "")
        if api_key and api_key != "your-api-key-here":
            self.client = anthropic.Anthropic(api_key=api_key)
            self.mock = False
        else:
            self.client = None
            self.mock = True

    def run(self, user_input: str, context: str = "general") -> PipelineResult:
        """
        Run the complete guardrail pipeline.

        Args:
            user_input: Raw user message
            context: Context type for validation rules

        Returns:
            PipelineResult with all stage results
        """
        stages = []
        total_start = time.perf_counter()

        # ── Stage 1: Input Validation ─────────────────────────
        stage1_start = time.perf_counter()
        validation = self.validator.validate(user_input, context=context)
        stage1_ms = (time.perf_counter() - stage1_start) * 1000

        stages.append({
            "stage": "input_validation",
            "passed": validation.is_safe,
            "threat": validation.threat_detected,
            "risk_score": validation.risk_score,
            "latency_ms": round(stage1_ms, 2)
        })

        # Block if validation failed and not sanitizable
        if not validation.is_safe and validation.sanitized_input is None:
            total_ms = (time.perf_counter() - total_start) * 1000
            return PipelineResult(
                original_input=user_input[:100],
                was_blocked=True,
                was_sanitized=False,
                block_reason=validation.threat_detected,
                ai_response=None,
                output_filtered=False,
                output_filter_reason=None,
                final_response=f"I cannot process this request. "
                               f"[{validation.threat_detected}]",
                total_latency_ms=round(total_ms, 1),
                stages=stages
            )

        # Use sanitized input if available
        safe_input = (
            validation.sanitized_input
            if validation.sanitized_input
            else user_input
        )
        was_sanitized = not validation.is_safe and validation.sanitized_input is not None

        # ── Stage 2: LLM Generation ───────────────────────────
        stage2_start = time.perf_counter()
        ai_response = self._call_llm(safe_input)
        stage2_ms = (time.perf_counter() - stage2_start) * 1000

        stages.append({
            "stage": "llm_generation",
            "passed": True,
            "mock": self.mock,
            "latency_ms": round(stage2_ms, 2)
        })

        # ── Stage 3: Output Filtering ─────────────────────────
        stage3_start = time.perf_counter()
        filter_result = self.output_filter.filter(ai_response)
        stage3_ms = (time.perf_counter() - stage3_start) * 1000

        stages.append({
            "stage": "output_filtering",
            "passed": filter_result.is_safe,
            "issue": filter_result.issue_detected,
            "redactions": filter_result.redactions_made,
            "latency_ms": round(stage3_ms, 2)
        })

        total_ms = (time.perf_counter() - total_start) * 1000

        return PipelineResult(
            original_input=user_input[:100],
            was_blocked=False,
            was_sanitized=was_sanitized,
            block_reason=None,
            ai_response=ai_response,
            output_filtered=not filter_result.is_safe,
            output_filter_reason=filter_result.issue_detected,
            final_response=filter_result.filtered_output,
            total_latency_ms=round(total_ms, 1),
            stages=stages
        )

    def _call_llm(self, user_input: str) -> str:
        """Call Claude or return a mock response."""
        if self.mock:
            return self._mock_response(user_input)

        try:
            response = self.client.messages.create(
                model="claude-sonnet-4-6",
                max_tokens=512,
                temperature=0.5,
                system=SYSTEM_PROMPT,
                messages=[{"role": "user", "content": user_input}]
            )
            return response.content[0].text
        except Exception as e:
            return f"I encountered an error processing your request: {str(e)[:100]}"

    def _mock_response(self, user_input: str) -> str:
        """Generate contextual mock response."""
        text = user_input.lower()
        if any(w in text for w in ["jwt", "token", "401", "auth"]):
            return ("JWT tokens expire after 30 minutes. Use POST /auth/refresh "
                    "with your refresh token to get a new access token.")
        if any(w in text for w in ["500", "error", "crash", "down"]):
            return ("Check your application logs first: docker logs app --tail 100. "
                    "Common causes: unhandled exceptions, DB connection failures.")
        if any(w in text for w in ["slow", "performance", "query"]):
            return ("Use EXPLAIN ANALYZE to check query plans. Add indexes on "
                    "columns used in WHERE clauses. Consider Redis caching.")
        return ("I can help with task management, debugging, performance, "
                "and deployment questions. What specific issue are you facing?")