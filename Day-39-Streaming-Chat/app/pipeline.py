# ============================================================
# app/pipeline.py
# Streaming pipeline with stage updates + KB retrieval
# ============================================================

import json
import asyncio
import time
from typing import AsyncGenerator

from app.knowledge_base import search_kb
from app.streamer import ClaudeStreamer

PIPELINE_SYSTEM = """You are a helpful AI assistant with access to technical documentation.
When context is provided, ground your answer in that documentation and cite it.
Be concise, specific, and use markdown formatting."""


class StreamingPipeline:
    """
    Multi-step pipeline that streams stage updates as it runs.

    The user sees:
    1. "Searching knowledge base..." (stage update)
    2. "Found 2 relevant articles" (stage update)
    3. "Generating answer..." (stage update)
    4. Token-by-token answer (streaming generation)
    5. Source citations (done event)
    """

    def __init__(self):
        self.streamer = ClaudeStreamer()

    async def run(
        self,
        query: str,
        history: list[dict] = None
    ) -> AsyncGenerator[str, None]:
        """
        Run the full RAG pipeline, streaming all stages.

        Yields SSE-formatted strings.
        """

        # ── Stage 1: Analysis ─────────────────────────────────
        yield f"data: {json.dumps({'type': 'stage', 'stage': 'analyzing', 'message': 'Analyzing your question...'})}\n\n"
        await asyncio.sleep(0.1)    # small delay so user sees the stage

        # ── Stage 2: KB Retrieval ─────────────────────────────
        yield f"data: {json.dumps({'type': 'stage', 'stage': 'retrieving', 'message': 'Searching knowledge base...'})}\n\n"

        # Run KB search (synchronous, wrap in thread)
        kb_results = search_kb(query, top_k=2)

        if kb_results:
            titles = [r["title"] for r in kb_results]
            yield f"data: {json.dumps({'type': 'stage', 'stage': 'retrieved', 'message': f'Found {len(kb_results)} relevant article(s)', 'articles': titles})}\n\n"
        else:
            yield f"data: {json.dumps({'type': 'stage', 'stage': 'retrieved', 'message': 'No KB matches — answering from general knowledge'})}\n\n"

        await asyncio.sleep(0.05)

        # ── Stage 3: Build augmented prompt ───────────────────
        if kb_results:
            context_parts = []
            for doc in kb_results:
                context_parts.append(f"[{doc['title']}]\n{doc['content']}")
            context = "\n\n---\n\n".join(context_parts)

            augmented_query = f"""KNOWLEDGE BASE CONTEXT:
{context}

---

USER QUESTION: {query}

Answer based on the context above. Cite the article you're drawing from."""
        else:
            augmented_query = query

        # ── Stage 4: Generation ───────────────────────────────
        yield f"data: {json.dumps({'type': 'stage', 'stage': 'generating', 'message': 'Generating answer...'})}\n\n"

        # Stream Claude tokens
        async for event in self.streamer.stream_response(augmented_query, history):
            yield f"data: {json.dumps(event)}\n\n"

            if event.get("type") == "done":
                # Add sources to the done event
                sources = [r["title"] for r in kb_results]
                done_with_sources = {**event, "sources": sources}
                # (already yielded above, add sources separately)
                yield f"data: {json.dumps({'type': 'sources', 'sources': sources})}\n\n"

        yield "data: [DONE]\n\n"