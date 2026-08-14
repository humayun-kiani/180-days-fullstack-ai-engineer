# ============================================================
# app/claude_client.py
# Anthropic API client with retry logic and cost tracking
# ============================================================

import os
import time
import json
import re
from typing import Optional, Generator
from dotenv import load_dotenv

load_dotenv()

try:
    import anthropic
    ANTHROPIC_AVAILABLE = True
except ImportError:
    ANTHROPIC_AVAILABLE = False


class MockAnthropicClient:
    """
    Mock client for when API key is not available.
    Returns realistic-looking responses for development/testing.
    """

    class MockMessage:
        def __init__(self, text: str, input_tokens: int = 100, output_tokens: int = 150):
            self.content = [type('obj', (object,), {'text': text})()]
            self.usage = type('obj', (object,), {
                'input_tokens': input_tokens,
                'output_tokens': output_tokens
            })()
            self.stop_reason = "end_turn"
            self.model = "claude-sonnet-4-6-mock"

    def messages_create(self, **kwargs) -> 'MockAnthropicClient.MockMessage':
        """Generate a mock response based on the user message."""
        messages = kwargs.get("messages", [])
        last_user_msg = ""
        for m in reversed(messages):
            if m["role"] == "user":
                last_user_msg = m["content"].lower()
                break

        # Generate contextual mock response
        if "500" in last_user_msg or "error" in last_user_msg:
            text = """Based on the knowledge base, here are the steps to debug API 500 errors:

1. **Check application logs immediately**: `docker logs container_name --tail 100`
2. **Enable DEBUG mode** to get full stack traces
3. **Common causes**: unhandled exceptions, database connection failures, missing environment variables

The most common cause in our system is database connection pool exhaustion. Check if PostgreSQL is accepting connections with: `SELECT count(*) FROM pg_stat_activity;`"""
        elif "jwt" in last_user_msg or "token" in last_user_msg or "401" in last_user_msg:
            text = """JWT token issues are a common source of 401 errors. Here's what to check:

1. **Token expiry**: Access tokens expire after **30 minutes** in our system
2. **Use the refresh endpoint**: `POST /api/v1/auth/refresh` with your refresh token
3. **Refresh tokens are ONE-TIME USE** — after refreshing, the old refresh token is invalidated
4. **Logout invalidation**: Tokens added to Redis blacklist on logout remain invalid until natural expiry

If both tokens expired (after 7 days inactivity), the user must log in again — this is expected behavior."""
        elif "slow" in last_user_msg or "performance" in last_user_msg:
            text = """For slow API performance, follow this diagnostic approach:

1. **Check X-Process-Time-Ms header** in response headers to identify slow endpoints
2. **Database queries**: Use `EXPLAIN ANALYZE` in PostgreSQL to find missing indexes
3. **N+1 queries**: Enable SQLAlchemy `echo=True` to see all SQL being executed
4. **Caching**: Implement Redis Cache-Aside pattern for frequently-read data
5. **External calls**: Ensure all HTTP calls have timeouts: `httpx.get(url, timeout=5.0)`"""
        else:
            text = f"""I found relevant information in the knowledge base for your question.

Based on our documentation: This topic is covered in our technical guides. The key points are:
- Follow the established patterns documented in our knowledge base
- Check the relevant configuration files and logs
- If the issue persists, escalate to the appropriate team

Is there a specific aspect you'd like me to elaborate on?"""

        return self.MockMessage(text, input_tokens=250, output_tokens=180)


class ClaudeClient:
    """
    Anthropic Claude API client.

    Wraps the official client with:
    - Automatic retry with exponential backoff
    - Token usage tracking
    - Cost estimation
    - Structured output extraction
    - Fallback to mock client when no API key
    """

    MODEL = "claude-sonnet-4-6"
    # Approximate costs per 1K tokens (update as pricing changes)
    COST_PER_1K_INPUT = 0.003
    COST_PER_1K_OUTPUT = 0.015

    def __init__(self):
        api_key = os.environ.get("ANTHROPIC_API_KEY", "")

        if ANTHROPIC_AVAILABLE and api_key and api_key != "your-api-key-here":
            self._client = anthropic.Anthropic(api_key=api_key)
            self._mock = False
            print("  ✅ Anthropic API client initialized")
        else:
            self._client = None
            self._mock = True
            print("  ⚠️  No API key — using mock client (add ANTHROPIC_API_KEY to .env)")

        # Session-level usage tracking
        self.total_input_tokens = 0
        self.total_output_tokens = 0
        self.total_calls = 0

    def complete(
        self,
        messages: list[dict],
        system: str = "",
        max_tokens: int = 1024,
        temperature: float = 0.7,
        max_retries: int = 3
    ) -> tuple[str, dict]:
        """
        Call Claude and return (response_text, usage_dict).

        Args:
            messages: Conversation messages.
            system: System prompt.
            max_tokens: Maximum output tokens.
            temperature: Randomness (0.0 = deterministic).
            max_retries: Retry attempts on transient failure.

        Returns:
            tuple: (response text, usage stats dict)
        """
        if self._mock:
            mock_response = MockAnthropicClient().messages_create(
                messages=messages,
                system=system,
                max_tokens=max_tokens
            )
            usage = {
                "input_tokens": mock_response.usage.input_tokens,
                "output_tokens": mock_response.usage.output_tokens,
                "estimated_cost_usd": self._estimate_cost(
                    mock_response.usage.input_tokens,
                    mock_response.usage.output_tokens
                )
            }
            self._track_usage(usage)
            return mock_response.content[0].text, usage

        # Real API call with retry
        delay = 1.0
        last_error = None

        for attempt in range(max_retries):
            try:
                kwargs = {
                    "model": self.MODEL,
                    "max_tokens": max_tokens,
                    "temperature": temperature,
                    "messages": messages
                }
                if system:
                    kwargs["system"] = system

                response = self._client.messages.create(**kwargs)

                usage = {
                    "input_tokens": response.usage.input_tokens,
                    "output_tokens": response.usage.output_tokens,
                    "estimated_cost_usd": self._estimate_cost(
                        response.usage.input_tokens,
                        response.usage.output_tokens
                    )
                }
                self._track_usage(usage)
                return response.content[0].text, usage

            except anthropic.RateLimitError as e:
                last_error = e
                if attempt < max_retries - 1:
                    print(f"  Rate limited. Waiting {delay}s... (attempt {attempt+1})")
                    time.sleep(delay)
                    delay *= 2

            except anthropic.APIStatusError as e:
                if e.status_code >= 500 and attempt < max_retries - 1:
                    time.sleep(delay)
                    delay *= 2
                    last_error = e
                else:
                    raise

            except Exception as e:
                last_error = e
                if attempt < max_retries - 1:
                    time.sleep(delay)
                    delay *= 2

        raise last_error or Exception("Max retries exceeded")

    def complete_structured(
        self,
        prompt: str,
        schema: str,
        system_prefix: str = "",
        max_tokens: int = 1024
    ) -> tuple[dict, dict]:
        """
        Get structured JSON output from Claude.

        Returns:
            tuple: (parsed_dict, usage_stats)
        """
        system = f"""{system_prefix}
You must respond with ONLY valid JSON matching this exact schema (no markdown, no extra text):
{schema}"""

        text, usage = self.complete(
            messages=[{"role": "user", "content": prompt}],
            system=system,
            max_tokens=max_tokens,
            temperature=0.1    # low temp for consistent structured output
        )

        return self._extract_json(text), usage

    def stream(
        self,
        messages: list[dict],
        system: str = "",
        max_tokens: int = 1024
    ) -> Generator[str, None, None]:
        """
        Stream response tokens one by one.

        Yields:
            str: Individual text tokens.
        """
        if self._mock:
            # Simulate streaming by chunking mock response
            mock = MockAnthropicClient().messages_create(
                messages=messages,
                system=system,
                max_tokens=max_tokens
            )
            text = mock.content[0].text
            words = text.split()
            for i, word in enumerate(words):
                yield word + (" " if i < len(words) - 1 else "")
                time.sleep(0.02)    # simulate token delay
            return

        kwargs = {
            "model": self.MODEL,
            "max_tokens": max_tokens,
            "messages": messages
        }
        if system:
            kwargs["system"] = system

        with self._client.messages.stream(**kwargs) as stream:
            for text in stream.text_stream:
                yield text

    def _extract_json(self, text: str) -> dict:
        """Extract JSON from LLM response, handling markdown blocks."""
        text = re.sub(r'```json\s*', '', text)
        text = re.sub(r'```\s*', '', text)
        text = text.strip()

        try:
            return json.loads(text)
        except json.JSONDecodeError:
            match = re.search(r'\{.*\}', text, re.DOTALL)
            if match:
                try:
                    return json.loads(match.group())
                except json.JSONDecodeError:
                    pass
            return {"error": "Failed to parse JSON", "raw": text[:200]}

    def _estimate_cost(self, input_tokens: int, output_tokens: int) -> float:
        """Estimate API cost in USD."""
        return (
            input_tokens / 1000 * self.COST_PER_1K_INPUT +
            output_tokens / 1000 * self.COST_PER_1K_OUTPUT
        )

    def _track_usage(self, usage: dict) -> None:
        """Accumulate token usage statistics."""
        self.total_input_tokens += usage.get("input_tokens", 0)
        self.total_output_tokens += usage.get("output_tokens", 0)
        self.total_calls += 1

    def get_session_stats(self) -> dict:
        """Get accumulated usage stats for this session."""
        total_cost = self._estimate_cost(
            self.total_input_tokens,
            self.total_output_tokens
        )
        return {
            "total_calls": self.total_calls,
            "total_input_tokens": self.total_input_tokens,
            "total_output_tokens": self.total_output_tokens,
            "total_tokens": self.total_input_tokens + self.total_output_tokens,
            "estimated_cost_usd": round(total_cost, 6)
        }