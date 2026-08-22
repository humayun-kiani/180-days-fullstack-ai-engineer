# ============================================================
# app/service.py
# Core AI service with graceful degradation
# ============================================================

import os
import json
import time
from enum import Enum
from typing import AsyncGenerator

import anthropic

from app.classifier import KeywordClassifier, MLClassifier, ClaudeClassifier
from app.guardrails import validate_input, filter_output
from app.metrics import MetricsStore, RequestRecord
from app.budget import TokenBudget


class ServiceMode(Enum):
    FULL = "full"
    DEGRADED = "degraded"


CLASSIFY_SYSTEM = """You are a task priority classifier.
Classify the task as: urgent, high, medium, or low.
Respond ONLY with valid JSON: {"priority": "...", "reason": "..."}"""

CHAT_SYSTEM = """You are a helpful AI assistant for a software development team.
Answer questions about debugging, authentication, performance, and deployment.
Be concise and practical."""


class ProductionAIService:
    """
    Production AI service with:
    - Graceful degradation
    - Guardrail pipeline
    - Token budget enforcement
    - Metrics collection
    - Streaming support
    """

    FAILURE_THRESHOLD = 3

    def __init__(self):
        api_key = os.environ.get("ANTHROPIC_API_KEY", "")
        self.mock = not (api_key and api_key != "your-api-key-here")

        if not self.mock:
            self.client = anthropic.Anthropic(api_key=api_key)
        else:
            self.client = None

        self.mode = ServiceMode.FULL
        self._failures = 0

        # Components
        self._keyword_clf = KeywordClassifier()
        self._ml_clf = MLClassifier()
        self._claude_clf = ClaudeClassifier(self.client)
        self.metrics = MetricsStore()
        self.budget = TokenBudget()

    # ── Classification ────────────────────────────────────────

    def classify(self, task: str, user_id: str = "anonymous") -> dict:
        """
        Classify task priority through the full production pipeline.
        """
        start = time.perf_counter()
        record = RequestRecord(
            timestamp=start,
            latency_ms=0,
            tokens_used=0,
            classifier_used="",
            was_blocked=False,
            was_degraded=False,
            output_filtered=False
        )

        # Stage 1: Input validation
        validation = validate_input(task)
        if not validation.safe:
            record.was_blocked = True
            record.classifier_used = "blocked"
            record.latency_ms = (time.perf_counter() - start) * 1000
            self.metrics.record(record)
            return {
                "status": "blocked",
                "reason": validation.threat,
                "priority": None,
                "latency_ms": round(record.latency_ms, 1)
            }

        safe_task = validation.safe_input or task

        # Stage 2: Mode-based classification
        if self.mode == ServiceMode.DEGRADED or self.mock:
            # Use ML classifier (no LLM needed)
            priority = self._ml_clf.predict(safe_task)
            classifier_used = self._ml_clf.name
            record.was_degraded = (self.mode == ServiceMode.DEGRADED)
            tokens = 0
        else:
            # Budget check
            estimated = len(safe_task.split()) * 3 + 50
            budget_check = self.budget.check(user_id, estimated)

            if not budget_check["allowed"]:
                # Fall back to ML when over budget
                priority = self._ml_clf.predict(safe_task)
                classifier_used = f"{self._ml_clf.name}:budget_fallback"
                record.was_degraded = True
                tokens = 0
            else:
                # Try Claude, fall back to ML on failure
                try:
                    result = self._classify_with_claude(safe_task)
                    priority = result.get("priority", "medium")
                    classifier_used = "claude_few_shot"
                    tokens = result.get("tokens", estimated)
                    self.budget.record(user_id, tokens)
                    self._failures = 0
                except Exception as e:
                    self._failures += 1
                    if self._failures >= self.FAILURE_THRESHOLD:
                        self.mode = ServiceMode.DEGRADED
                    priority = self._ml_clf.predict(safe_task)
                    classifier_used = f"{self._ml_clf.name}:llm_failed"
                    record.was_degraded = True
                    tokens = 0

        record.classifier_used = classifier_used
        record.tokens_used = tokens
        record.latency_ms = (time.perf_counter() - start) * 1000
        self.metrics.record(record)

        return {
            "status": "ok",
            "priority": priority,
            "classifier": classifier_used,
            "degraded": record.was_degraded,
            "latency_ms": round(record.latency_ms, 1)
        }

    def _classify_with_claude(self, task: str) -> dict:
        """Call Claude for classification. Returns dict with priority + tokens."""
        if self.client is None:
            raise RuntimeError("No Claude client")

        r = self.client.messages.create(
            model="claude-sonnet-4-6",
            max_tokens=50,
            temperature=0.0,
            system=CLASSIFY_SYSTEM,
            messages=[{"role": "user", "content": f"Classify: {task}"}]
        )

        text = r.content[0].text.strip()
        try:
            data = json.loads(text)
            priority = data.get("priority", "medium")
        except json.JSONDecodeError:
            import re
            match = re.search(r'\b(urgent|high|medium|low)\b', text.lower())
            priority = match.group(1) if match else "medium"

        return {
            "priority": priority,
            "tokens": r.usage.input_tokens + r.usage.output_tokens
        }

    # ── Streaming Chat ────────────────────────────────────────

    async def stream_chat(
        self,
        message: str,
        history: list[dict] = None,
        user_id: str = "anonymous"
    ) -> AsyncGenerator[dict, None]:
        """Stream chat response through the guardrail pipeline."""
        import asyncio

        start = time.perf_counter()
        record = RequestRecord(
            timestamp=start,
            latency_ms=0,
            tokens_used=0,
            classifier_used="claude_chat",
            was_blocked=False,
            was_degraded=False,
            output_filtered=False
        )

        # Stage 1: Input validation
        validation = validate_input(message)
        if not validation.safe:
            record.was_blocked = True
            record.latency_ms = (time.perf_counter() - start) * 1000
            self.metrics.record(record)
            yield {"type": "blocked", "reason": validation.threat}
            return

        safe_message = validation.safe_input or message

        # Stage 2: Budget check
        estimated = len(safe_message.split()) * 3 + 500
        budget_check = self.budget.check(user_id, estimated)
        if not budget_check["allowed"]:
            yield {"type": "error",
                   "message": f"Token budget exceeded: {budget_check['reason']}"}
            return

        # Stage 3: Stream (with fallback)
        yield {"type": "start", "mode": self.mode.value, "mock": self.mock}

        if self.mock:
            # Mock streaming
            responses = {
                "jwt": "JWT tokens expire after 30 minutes. Use POST /auth/refresh to get a new access token using your refresh token.",
                "500": "Check your logs first: docker logs container --tail 100. Common causes: unhandled exceptions, DB connection failures.",
                "slow": "Add EXPLAIN ANALYZE to find slow queries. Add indexes. Use Redis Cache-Aside for hot data.",
            }
            msg_lower = safe_message.lower()
            text = next(
                (v for k, v in responses.items() if k in msg_lower),
                "I can help with debugging, auth, performance, and deployment."
            )
            words = text.split()
            for i, word in enumerate(words):
                yield {"type": "token", "content": word + (" " if i < len(words)-1 else "")}
                await asyncio.sleep(0.04)

            record.tokens_used = len(words) * 2
            record.latency_ms = (time.perf_counter() - start) * 1000
            self.metrics.record(record)
            self.budget.record(user_id, record.tokens_used)
            yield {"type": "done", "tokens": record.tokens_used, "mock": True}
            return

        # Real streaming
        messages = list(history or [])
        messages.append({"role": "user", "content": safe_message})
        full_response = []

        try:
            with self.client.messages.stream(
                model="claude-sonnet-4-6",
                max_tokens=1024,
                system=CHAT_SYSTEM,
                messages=messages
            ) as stream:
                for text in stream.text_stream:
                    full_response.append(text)
                    yield {"type": "token", "content": text}

                final = stream.get_final_message()
                tokens_used = final.usage.output_tokens + final.usage.input_tokens

        except Exception as e:
            record.error = str(e)[:100]
            record.was_degraded = True
            yield {"type": "error", "message": f"Stream error: {str(e)[:80]}"}
            record.latency_ms = (time.perf_counter() - start) * 1000
            self.metrics.record(record)
            return

        # Stage 4: Filter full response
        complete_text = "".join(full_response)
        filtered_text, issues = filter_output(complete_text)

        if issues:
            record.output_filtered = True
            # Signal the client that the last output was filtered
            yield {"type": "filter_applied", "issues": issues}

        record.tokens_used = tokens_used
        self.budget.record(user_id, tokens_used)
        record.latency_ms = (time.perf_counter() - start) * 1000
        self.metrics.record(record)

        yield {"type": "done", "tokens": tokens_used,
               "latency_ms": round(record.latency_ms, 1)}