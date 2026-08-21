# ============================================================
# app/streamer.py
# Core streaming utilities for Claude API integration
# ============================================================

import os
import json
import time
import asyncio
from typing import AsyncGenerator

import anthropic

SYSTEM_PROMPT = """You are a helpful AI assistant for a software development team.
Answer questions about debugging, authentication, performance, databases, and deployment.
Be concise and practical. Use markdown formatting where helpful."""


class MockStreamer:
    """Stream realistic fake tokens when no API key is available."""

    RESPONSES = {
        "jwt": "**JWT tokens expire after 30 minutes** in your system.\n\nTo fix 401 errors:\n\n1. **Check expiry**: Decode the JWT and compare the `exp` field with current time\n2. **Use refresh endpoint**: `POST /api/v1/auth/refresh` with your refresh token\n3. **Store securely**: Keep refresh tokens in httpOnly cookies, never localStorage\n\nRefresh tokens last **7 days** and are ONE-TIME USE — after refreshing, the old token is automatically invalidated.",
        "500": "**HTTP 500 errors** usually come from unhandled exceptions.\n\n**Step 1: Check logs**\n```bash\ndocker logs your-container --tail 100\n```\n\n**Common causes:**\n- Unhandled exceptions in route handlers\n- Database connection failures\n- Missing environment variables\n- Memory issues\n\nAdd `try/except` blocks around database calls and log the full traceback with `request_id` for tracing.",
        "slow": "**Slow API responses** are usually caused by:\n\n1. **N+1 queries** — use `joinedload()` or `select_related()`\n2. **Missing indexes** — run `EXPLAIN ANALYZE` in PostgreSQL\n3. **No caching** — add Redis Cache-Aside for frequently-read data\n4. **External calls** — add timeout: `httpx.get(url, timeout=5.0)`\n\nCheck the `X-Process-Time-Ms` header to identify the slowest endpoints.",
        "default": "I can help with **debugging, authentication, performance, database configuration, Docker, testing**, and more.\n\nWhat specific technical issue are you facing? The more detail you provide, the more specific my answer can be."
    }

    async def stream_response(
        self,
        message: str,
        history: list[dict] = None
    ) -> AsyncGenerator[dict, None]:
        """Yield events simulating a streaming Claude response."""
        msg_lower = message.lower()

        if any(w in msg_lower for w in ["jwt", "token", "401", "auth"]):
            text = self.RESPONSES["jwt"]
        elif any(w in msg_lower for w in ["500", "error", "crash", "exception"]):
            text = self.RESPONSES["500"]
        elif any(w in msg_lower for w in ["slow", "performance", "latency", "query"]):
            text = self.RESPONSES["slow"]
        else:
            text = self.RESPONSES["default"]

        yield {"type": "start", "mock": True}

        # Simulate token-by-token streaming
        words = text.split(" ")
        for i, word in enumerate(words):
            token = word + (" " if i < len(words) - 1 else "")
            yield {"type": "token", "content": token}
            await asyncio.sleep(0.03)    # simulate generation delay

        yield {"type": "done", "tokens_generated": len(words), "mock": True}


class ClaudeStreamer:
    """Stream real Claude responses token by token."""

    def __init__(self):
        api_key = os.environ.get("ANTHROPIC_API_KEY", "")
        if api_key and api_key != "your-api-key-here":
            self.client = anthropic.Anthropic(api_key=api_key)
            self.mock = False
        else:
            self.client = None
            self.mock = True
            self._mock = MockStreamer()

    async def stream_response(
        self,
        message: str,
        history: list[dict] = None,
        max_tokens: int = 1024,
        temperature: float = 0.5
    ) -> AsyncGenerator[dict, None]:
        """
        Stream a Claude response as async generator of event dicts.

        Each yielded dict has:
          {"type": "start"} — stream beginning
          {"type": "token", "content": "..."} — one text chunk
          {"type": "done", "tokens_generated": N} — stream complete

        Args:
            message: User's message
            history: Prior conversation messages
            max_tokens: Maximum output length
            temperature: Generation randomness

        Yields:
            dict: Stream events
        """
        if self.mock:
            async for event in self._mock.stream_response(message, history):
                yield event
            return

        # Build messages list
        messages = list(history or [])
        messages.append({"role": "user", "content": message})

        yield {"type": "start", "mock": False}

        token_count = 0
        try:
            with self.client.messages.stream(
                model="claude-sonnet-4-6",
                max_tokens=max_tokens,
                temperature=temperature,
                system=SYSTEM_PROMPT,
                messages=messages
            ) as stream:
                for text in stream.text_stream:
                    yield {"type": "token", "content": text}
                    token_count += 1

                final = stream.get_final_message()
                token_count = final.usage.output_tokens

        except anthropic.RateLimitError:
            yield {"type": "error", "message": "Rate limit reached. Please wait a moment."}
            return
        except anthropic.APIConnectionError:
            yield {"type": "error", "message": "Connection error. Check your internet connection."}
            return
        except Exception as e:
            yield {"type": "error", "message": f"Error: {str(e)[:100]}"}
            return

        yield {"type": "done", "tokens_generated": token_count}


def events_to_sse(events: AsyncGenerator[dict, None]) -> AsyncGenerator[str, None]:
    """Convert event dicts to SSE-formatted strings."""
    async def generator():
        async for event in events:
            yield f"data: {json.dumps(event)}\n\n"
        yield "data: [DONE]\n\n"
    return generator()