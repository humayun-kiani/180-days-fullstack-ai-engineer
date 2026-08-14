# ============================================================
# app/main.py
# RAG Chatbot API — Day 32
# ============================================================

import json
import time
from contextlib import asynccontextmanager
from datetime import datetime
from typing import Optional

from fastapi import FastAPI, HTTPException, Query
from fastapi.responses import StreamingResponse

from app.schemas import (
    ChatRequest, ChatResponse,
    TaskAnalysisRequest, TaskAnalysisResponse
)
from app.claude_client import ClaudeClient
from app.rag_pipeline import RAGPipeline
from app.task_analyzer import TaskAnalyzer
from app.conversation import session_store


# ─── Global Services ─────────────────────────────────────────

_claude: ClaudeClient = None
_rag: RAGPipeline = None
_analyzer: TaskAnalyzer = None


def get_claude() -> ClaudeClient:
    if _claude is None:
        raise HTTPException(503, "Claude client not initialized")
    return _claude


def get_rag() -> RAGPipeline:
    if _rag is None:
        raise HTTPException(503, "RAG pipeline not initialized")
    return _rag


# ─── Startup ─────────────────────────────────────────────────

@asynccontextmanager
async def lifespan(app: FastAPI):
    global _claude, _rag, _analyzer

    print("\n" + "=" * 60)
    print("  RAG Chatbot with Claude — Day 32")
    print("  LLM Integration: Anthropic API + ChromaDB")
    print("=" * 60)

    print("\n  Initializing services...")
    _claude = ClaudeClient()
    _rag = RAGPipeline(_claude)
    _analyzer = TaskAnalyzer(_claude)

    print(f"\n  ✅ Ready!")
    print(f"  Docs: http://localhost:8000/docs\n")

    yield

    print("\n  Session stats:")
    stats = _claude.get_session_stats()
    for k, v in stats.items():
        print(f"    {k}: {v}")
    print("\n  Shutting down...")


# ─── App ─────────────────────────────────────────────────────

app = FastAPI(
    title="RAG Chatbot with Claude",
    description="""
## 🤖 RAG Chatbot — Day 32

A complete Retrieval-Augmented Generation chatbot powered by **Claude (Anthropic)**.

### How it works
1. **Retrieve**: ChromaDB finds relevant knowledge base articles (Day 31)
2. **Augment**: Retrieved context is added to the Claude prompt
3. **Generate**: Claude produces a grounded, accurate answer

### Endpoints
| Endpoint | Description |
|----------|-------------|
| `POST /chat` | Single or multi-turn chat with RAG |
| `POST /chat/stream` | Streaming chat response |
| `POST /analyze/task` | Structured task analysis (JSON output) |
| `GET /sessions/{id}` | Get conversation history |
| `GET /usage` | Token usage and cost stats |
| `GET /demo` | Run example queries |

### Setup
Add `ANTHROPIC_API_KEY=your-key` to `.env` for real Claude responses.
Without it, a mock client returns realistic demo responses.
    """,
    version="1.0.0",
    lifespan=lifespan
)


# ─── Chat Endpoints ───────────────────────────────────────────

@app.post(
    "/chat",
    response_model=ChatResponse,
    summary="Chat with the RAG knowledge base",
    description="""
Ask questions and get answers grounded in the knowledge base.

Supports multi-turn conversation via `session_id`.
Set `use_knowledge_base: false` for direct Claude answers without retrieval.
    """
)
def chat(request: ChatRequest) -> ChatResponse:
    """Main chat endpoint with RAG."""
    rag = get_rag()
    start = time.perf_counter()

    # Get or create session
    session = session_store.get_or_create(request.session_id)
    session.add_user_message(request.message)

    # Get conversation history
    history = session.get_api_messages()

    # Generate answer via RAG
    answer, sources, usage = rag.answer(
        question=request.message,
        conversation_messages=history[:-1],    # history without current message
        use_kb=request.use_knowledge_base,
        temperature=0.5
    )

    # Update session
    session.add_assistant_message(
        answer,
        tokens=usage.get("output_tokens", 0)
    )

    elapsed_ms = (time.perf_counter() - start) * 1000
    usage["latency_ms"] = round(elapsed_ms, 1)

    return ChatResponse(
        answer=answer,
        session_id=session.session_id,
        sources=sources,
        tokens_used=usage,
        retrieved_context=len(sources) > 0,
        model=_claude.MODEL if not _claude._mock else "mock"
    )


@app.post(
    "/chat/stream",
    summary="Streaming chat response",
    description="Same as /chat but streams tokens as they are generated (SSE format)."
)
def chat_stream(request: ChatRequest):
    """Stream chat response token by token."""
    rag = get_rag()
    session = session_store.get_or_create(request.session_id)
    session.add_user_message(request.message)
    history = session.get_api_messages()

    def generate():
        full_response = []

        # Stream tokens
        for token in rag.stream_answer(
            question=request.message,
            conversation_messages=history[:-1],
            use_kb=request.use_knowledge_base
        ):
            full_response.append(token)
            yield f"data: {json.dumps({'token': token, 'session_id': session.session_id})}\n\n"

        # Final message with metadata
        complete_text = "".join(full_response)
        session.add_assistant_message(complete_text)

        yield f"data: {json.dumps({'done': True, 'session_id': session.session_id})}\n\n"
        yield "data: [DONE]\n\n"

    return StreamingResponse(generate(), media_type="text/event-stream")


# ─── Task Analysis Endpoint ───────────────────────────────────

@app.post(
    "/analyze/task",
    response_model=TaskAnalysisResponse,
    summary="Structured task analysis",
    description="""
Analyze a task description and get structured JSON output from Claude.

Returns: priority, category, estimated hours, tags, suggested actions, urgency score.

Uses few-shot prompting and temperature=0.1 for consistent JSON output.
    """
)
def analyze_task(request: TaskAnalysisRequest) -> TaskAnalysisResponse:
    """Get structured task analysis from Claude."""
    if _analyzer is None:
        raise HTTPException(503, "Analyzer not initialized")

    result, tokens = _analyzer.analyze(
        title=request.title,
        description=request.description or ""
    )

    return TaskAnalysisResponse(
        priority=result.get("priority", "medium"),
        category=result.get("category", "general"),
        estimated_hours=float(result.get("estimated_hours", 4.0)),
        tags=result.get("tags", []),
        reason=result.get("reason", ""),
        suggested_actions=result.get("suggested_actions", []),
        urgency_score=int(result.get("urgency_score", 5)),
        model=_claude.MODEL if not _claude._mock else "mock",
        tokens_used=tokens
    )


# ─── Session Endpoints ────────────────────────────────────────

@app.get("/sessions", summary="List all sessions")
def list_sessions():
    return {"sessions": session_store.list_sessions()}


@app.get("/sessions/{session_id}", summary="Get session details")
def get_session(session_id: str):
    session = session_store.get(session_id)
    if not session:
        raise HTTPException(404, f"Session '{session_id}' not found")
    return {
        **session.to_dict(),
        "messages": [
            {"role": m.role, "content": m.content[:200] + "...", "timestamp": m.timestamp}
            for m in session.messages
        ]
    }


@app.delete("/sessions/{session_id}", summary="Delete a session")
def delete_session(session_id: str):
    if session_store.delete(session_id):
        return {"message": f"Session '{session_id}' deleted"}
    raise HTTPException(404, f"Session '{session_id}' not found")


# ─── Usage and Stats ──────────────────────────────────────────

@app.get("/usage", summary="Token usage and cost statistics")
def get_usage():
    """Get accumulated token usage and estimated cost for this server session."""
    if _claude is None:
        raise HTTPException(503, "Claude not initialized")
    return {
        **_claude.get_session_stats(),
        "model": _claude.MODEL,
        "is_mock": _claude._mock,
        "timestamp": datetime.utcnow().isoformat()
    }


# ─── Demo Endpoint ────────────────────────────────────────────

@app.get("/demo", summary="Run example queries to see RAG in action")
def demo():
    """Run several demo queries and return results."""
    rag = get_rag()

    demo_questions = [
        "My API keeps returning 401 errors after users log in",
        "The application is running very slowly after the latest deployment",
        "Docker container keeps restarting",
        "How do I handle database connections efficiently?",
        "Celery tasks are not running",
    ]

    results = []
    for question in demo_questions:
        sources, context = rag.retrieve(question)
        results.append({
            "question": question,
            "top_source": sources[0]["title"] if sources else "No match",
            "relevance_score": sources[0]["relevance_score"] if sources else 0,
            "retrieved": len(sources) > 0
        })

    return {
        "message": "Demo RAG retrieval results (answer generation requires API key)",
        "demos": results,
        "insight": "Semantic search finds relevant articles even when query words don't match article keywords"
    }


# ─── Health ───────────────────────────────────────────────────

@app.get("/health")
def health():
    return {
        "status": "healthy",
        "claude_mock": _claude._mock if _claude else True,
        "kb_available": _rag._collection is not None if _rag else False,
        "model": _claude.MODEL if _claude else "none",
        "timestamp": datetime.utcnow().isoformat(),
        "day": "Day 32 — LLM Integration & RAG Chatbot"
    }


@app.get("/")
def root():
    return {
        "name": "RAG Chatbot with Claude",
        "day": "Day 32 — LLM Integration, Prompt Engineering & RAG",
        "docs": "/docs",
        "demo": "/demo",
        "usage": "/usage"
    }