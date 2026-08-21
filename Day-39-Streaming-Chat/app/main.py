# ============================================================
# app/main.py
# Streaming AI Chat — Day 39
# ============================================================

import json
import asyncio
import time
from contextlib import asynccontextmanager
from datetime import datetime

from fastapi import FastAPI, Request, HTTPException
from fastapi.responses import StreamingResponse, HTMLResponse, FileResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, Field
from dotenv import load_dotenv

load_dotenv()

from app.streamer import ClaudeStreamer
from app.pipeline import StreamingPipeline

_streamer: ClaudeStreamer = None
_pipeline: StreamingPipeline = None


@asynccontextmanager
async def lifespan(app: FastAPI):
    global _streamer, _pipeline

    print("\n" + "=" * 60)
    print("  Streaming AI Chat — Day 39")
    print("  Real-Time Responses with SSE + RAG Pipeline")
    print("=" * 60)

    _streamer = ClaudeStreamer()
    _pipeline = StreamingPipeline()

    mode = "Mock (no API key)" if _streamer.mock else "Real Claude API"
    print(f"\n  Mode: {mode}")
    print(f"  Chat UI: http://localhost:8000")
    print(f"  Docs:    http://localhost:8000/docs\n")

    yield
    print("\n  Shutting down...")


app = FastAPI(
    title="Streaming AI Chat",
    description="""
## 💬 Real-Time Streaming AI Chat — Day 39

Token-by-token streaming with SSE (Server-Sent Events).

### Endpoints
| Endpoint | Description |
|----------|-------------|
| `GET /` | Web chat interface |
| `POST /stream/chat` | Direct streaming chat |
| `POST /stream/pipeline` | RAG pipeline with stage updates |
| `GET /stream/demo` | Demo stream (no input needed) |

### How Streaming Works
1. Client sends POST request with message
2. Server opens SSE stream (text/event-stream)
3. Server yields JSON events as tokens arrive from Claude
4. Client appends tokens to UI in real-time
5. Stream ends with [DONE] marker

### Event Types
```json
{"type": "start"}
{"type": "stage", "stage": "retrieving", "message": "..."}
{"type": "token", "content": "Hello"}
{"type": "sources", "sources": ["JWT Guide"]}
{"type": "done", "tokens_generated": 142}
{"type": "error", "message": "..."}
```
    """,
    version="1.0.0",
    lifespan=lifespan
)

app.mount("/static", StaticFiles(directory="static"), name="static")


# ─── Schemas ─────────────────────────────────────────────────

class ChatRequest(BaseModel):
    message: str = Field(min_length=1, max_length=5000)
    history: list[dict] = Field(default=[])

    class Config:
        json_schema_extra = {
            "example": {
                "message": "How do I fix JWT expiration errors?",
                "history": []
            }
        }


# ─── Web UI ───────────────────────────────────────────────────

@app.get("/", response_class=HTMLResponse)
async def chat_ui():
    """Serve the web chat interface."""
    with open("static/index.html") as f:
        return f.read()


# ─── Streaming Endpoints ──────────────────────────────────────

@app.post(
    "/stream/chat",
    summary="Direct streaming chat — no retrieval, just Claude",
    description="Streams Claude's response token by token. No knowledge base retrieval."
)
async def stream_chat(request: ChatRequest, req: Request):
    """Stream a direct Claude response."""

    async def generate():
        try:
            async for event in _streamer.stream_response(
                message=request.message,
                history=request.history
            ):
                # Check if client disconnected
                if await req.is_disconnected():
                    break
                yield f"data: {json.dumps(event)}\n\n"
            yield "data: [DONE]\n\n"
        except Exception as e:
            yield f"data: {json.dumps({'type': 'error', 'message': str(e)[:100]})}\n\n"
            yield "data: [DONE]\n\n"

    return StreamingResponse(
        generate(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "X-Accel-Buffering": "no",
            "Connection": "keep-alive",
            "Access-Control-Allow-Origin": "*",
        }
    )


@app.post(
    "/stream/pipeline",
    summary="RAG pipeline with stage streaming",
    description="""
Streams stage updates + tokens from the full RAG pipeline:
1. Analyzing query
2. Searching knowledge base
3. Generating answer with context

Watch stage updates appear before the answer starts streaming.
    """
)
async def stream_pipeline(request: ChatRequest, req: Request):
    """Stream the full RAG pipeline with stage updates."""

    async def generate():
        try:
            async for chunk in _pipeline.run(
                query=request.message,
                history=request.history
            ):
                if await req.is_disconnected():
                    break
                yield chunk
        except Exception as e:
            yield f"data: {json.dumps({'type': 'error', 'message': str(e)[:100]})}\n\n"
            yield "data: [DONE]\n\n"

    return StreamingResponse(
        generate(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "X-Accel-Buffering": "no",
            "Connection": "keep-alive",
        }
    )


@app.get(
    "/stream/demo",
    summary="Demo — stream a pre-written response"
)
async def stream_demo():
    """
    Demo endpoint: streams a fixed response without calling Claude.
    Shows the SSE format and timing.
    """
    async def generate():
        tokens = [
            "Server-Sent Events ", "allow the server ", "to push data ",
            "to the browser ", "without the client ", "asking for it.\n\n",
            "This is how ", "ChatGPT and Claude.ai ", "show responses ",
            "as they are generated: ", "token by token, ", "in real time.",
        ]

        yield f"data: {json.dumps({'type': 'start', 'demo': True})}\n\n"
        await asyncio.sleep(0.2)

        for token in tokens:
            yield f"data: {json.dumps({'type': 'token', 'content': token})}\n\n"
            await asyncio.sleep(0.08)

        yield f"data: {json.dumps({'type': 'done', 'tokens_generated': len(tokens), 'demo': True})}\n\n"
        yield "data: [DONE]\n\n"

    return StreamingResponse(
        generate(),
        media_type="text/event-stream",
        headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no"}
    )


@app.post(
    "/stream/pipeline/steps",
    summary="Show pipeline steps without generating"
)
async def stream_pipeline_steps(message: str = "How do I fix JWT errors?"):
    """Show only the pipeline analysis and retrieval stages — no Claude generation."""
    from app.knowledge_base import search_kb

    async def generate():
        yield f"data: {json.dumps({'type': 'stage', 'stage': 'start', 'message': 'Starting pipeline...'})}\n\n"
        await asyncio.sleep(0.3)

        yield f"data: {json.dumps({'type': 'stage', 'stage': 'analyzing', 'message': f'Analyzing: {message[:50]}'})}\n\n"
        await asyncio.sleep(0.3)

        results = search_kb(message)
        titles = [r["title"] for r in results]

        if results:
            yield f"data: {json.dumps({'type': 'stage', 'stage': 'retrieved', 'message': f'Found {len(results)} KB articles', 'articles': titles})}\n\n"
        else:
            yield f"data: {json.dumps({'type': 'stage', 'stage': 'retrieved', 'message': 'No KB matches found'})}\n\n"

        await asyncio.sleep(0.3)

        yield f"data: {json.dumps({'type': 'stage', 'stage': 'would_generate', 'message': 'Would now generate with Claude (skipped in this demo)'})}\n\n"
        yield f"data: {json.dumps({'type': 'done', 'kb_articles': titles})}\n\n"
        yield "data: [DONE]\n\n"

    return StreamingResponse(generate(), media_type="text/event-stream",
                             headers={"Cache-Control": "no-cache"})


# ─── Health ───────────────────────────────────────────────────

@app.get("/health")
def health() -> dict:
    return {
        "status": "healthy",
        "mock": _streamer.mock if _streamer else True,
        "streaming": True,
        "endpoints": ["/stream/chat", "/stream/pipeline", "/stream/demo"],
        "timestamp": datetime.utcnow().isoformat(),
        "day": "Day 39 — Streaming AI Responses & Real-Time UX"
    }


@app.get("/api/kb/search")
def kb_search(q: str = "jwt expiration") -> dict:
    """Test knowledge base search without streaming."""
    from app.knowledge_base import search_kb
    results = search_kb(q)
    return {"query": q, "results": results, "count": len(results)}