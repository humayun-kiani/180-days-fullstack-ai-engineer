# ============================================================
# app/main.py
# AI Research Assistant — Day 36: Week 6 Integration
# ============================================================

import asyncio
import time
from contextlib import asynccontextmanager
from datetime import datetime
from typing import Optional

from fastapi import FastAPI, HTTPException, Query
from pydantic import BaseModel, Field
from dotenv import load_dotenv

load_dotenv()

from app.router import analyze_query
from app.pipeline import ResearchPipeline
from app.generator import ClaudeGenerator


_pipeline: ResearchPipeline = None
_generator: ClaudeGenerator = None


@asynccontextmanager
async def lifespan(app: FastAPI):
    global _pipeline, _generator

    print("\n" + "=" * 60)
    print("  AI Research Assistant — Day 36")
    print("  Week 6 Integration: Days 31-35 Unified")
    print("=" * 60)

    _pipeline = ResearchPipeline()
    _generator = ClaudeGenerator()

    mode = "Mock" if _generator.mock else "Real (Claude API)"
    print(f"\n  Generator: {mode}")
    print(f"  Pipeline: KB + Weather + GitHub + Rates + HackerNews + Tasks")
    print(f"\n  Docs: http://localhost:8000/docs\n")
    yield
    print("\n  Shutting down...")


app = FastAPI(
    title="AI Research Assistant",
    description="""
## 🔬 AI Research Assistant — Day 36: Week 6 Integration

Unifies all Week 6 components into a single pipeline:

| Day | Component | What it adds |
|-----|-----------|-------------|
| 31 | ChromaDB Embeddings | Semantic KB search |
| 32 | RAG with Claude | Grounded generation |
| 33 | LangChain Agent | Tool orchestration |
| 34 | Raw Tool Calling | Direct API control |
| 35 | External APIs | Real-time live data |
| **36** | **Integration** | **Unified pipeline** |

### Pipeline Flow