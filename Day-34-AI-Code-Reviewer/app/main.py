# ============================================================
# app/main.py
# AI Code Reviewer FastAPI application
# Day 34 — AI Function Calling & Tool Use
# ============================================================

import json
import os
import time
from contextlib import asynccontextmanager
from datetime import datetime

from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException
from fastapi.responses import JSONResponse

from app.schemas import CodeReview, ReviewRequest, InlineReviewRequest
from app.review_tools import registry
from app.reviewer import AICodeReviewer

load_dotenv()

_reviewer: AICodeReviewer = None


@asynccontextmanager
async def lifespan(app: FastAPI):
    global _reviewer

    print("\n" + "=" * 60)
    print("  AI Code Reviewer — Day 34")
    print("  Raw Anthropic Tool Use + Custom Tool Registry")
    print("=" * 60)

    _reviewer = AICodeReviewer(registry)
    mode = "Mock (no API key)" if _reviewer.mock else "Real (Claude API)"
    print(f"\n  Mode: {mode}")
    print(f"  Registered tools: {registry.tool_names}")
    print(f"  Sample files: sample_code/bad_code.py, sample_code/good_code.py")
    print(f"\n  Docs: http://localhost:8000/docs\n")

    yield
    print("\n  Shutting down...")


app = FastAPI(
    title="AI Code Reviewer",
    description="""
## 🔍 AI Code Reviewer — Day 34

Uses **raw Anthropic tool calling** (no LangChain) to review Python code.

### How it works
1. Claude receives the file path and tool schemas
2. Claude decides which tools to call and in what order:
   - `read_file` — get the code content
   - `compute_code_metrics` — line counts, complexity
   - `find_security_issues` — hardcoded creds, SQL injection
   - `find_style_issues` — PEP 8, naming conventions
   - `find_performance_issues` — nested loops, blocking calls
3. Tool results are fed back to Claude
4. Claude synthesizes a final structured review

### This demonstrates
- Raw Anthropic `tool_use` stop reason handling
- Custom `ToolRegistry` pattern
- Multi-step agentic loop without LangChain
- Parallel tool result collection
- Structured output from tool calling agents
    """,
    version="1.0.0",
    lifespan=lifespan
)


@app.post(
    "/review/file",
    response_model=CodeReview,
    summary="Review a Python file",
    description="Provide a file path and the AI agent will analyze it with 5 specialized tools."
)
def review_file(request: ReviewRequest) -> CodeReview:
    """Review a Python file using the AI agent."""
    if _reviewer is None:
        raise HTTPException(503, "Reviewer not initialized")

    # Security: only allow files in sample_code directory
    if ".." in request.file_path or request.file_path.startswith("/"):
        raise HTTPException(400, "Only relative paths within the project are allowed")

    try:
        review = _reviewer.review(
            file_path=request.file_path,
            focus_areas=request.focus_areas
        )
        return review
    except FileNotFoundError:
        raise HTTPException(404, f"File not found: {request.file_path}")
    except Exception as e:
        raise HTTPException(500, f"Review failed: {str(e)}")


@app.post(
    "/review/inline",
    response_model=CodeReview,
    summary="Review inline code",
    description="Provide code as a string and receive a full AI review."
)
def review_inline(request: InlineReviewRequest) -> CodeReview:
    """Review code provided as a string."""
    if _reviewer is None:
        raise HTTPException(503, "Reviewer not initialized")
    try:
        return _reviewer.review_inline(
            code=request.code,
            filename=request.filename
        )
    except Exception as e:
        raise HTTPException(500, f"Review failed: {str(e)}")


@app.get(
    "/review/demo",
    response_model=CodeReview,
    summary="Demo — review sample bad code"
)
def review_demo() -> CodeReview:
    """Run the reviewer on the included bad_code.py sample."""
    if _reviewer is None:
        raise HTTPException(503, "Reviewer not initialized")
    return _reviewer.review("sample_code/bad_code.py")


@app.get(
    "/tools",
    summary="List registered tools and their schemas"
)
def list_tools() -> dict:
    """Show all tools available to the AI reviewer."""
    return {
        "tools": registry.get_all_schemas(),
        "count": len(registry.tool_names),
        "tool_names": registry.tool_names
    }


@app.get(
    "/tools/call-log",
    summary="Get the tool call history"
)
def tool_call_log() -> dict:
    """Get the log of all tool calls made in the last review."""
    return {
        "call_log": registry.get_call_log(),
        "total_calls": len(registry.get_call_log())
    }


@app.get("/health")
def health() -> dict:
    return {
        "status": "healthy",
        "mode": "mock" if (_reviewer and _reviewer.mock) else "real",
        "tools": registry.tool_names,
        "timestamp": datetime.utcnow().isoformat(),
        "day": "Day 34 — AI Function Calling & Tool Use"
    }


@app.get("/")
def root() -> dict:
    return {
        "name": "AI Code Reviewer",
        "day": "Day 34 — Raw Tool Use, Custom Registry",
        "docs": "/docs",
        "demo": "/review/demo",
        "endpoints": {
            "review_file": "POST /review/file",
            "review_inline": "POST /review/inline",
            "demo": "GET /review/demo",
            "tools": "GET /tools",
            "call_log": "GET /tools/call-log"
        }
    }