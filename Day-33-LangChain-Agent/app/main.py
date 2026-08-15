# ============================================================
# app/main.py
# LangChain Agent API — Day 33
# ============================================================

import os
import time
from contextlib import asynccontextmanager
from datetime import datetime
from typing import Optional

from fastapi import FastAPI, HTTPException
from fastapi.responses import StreamingResponse
from pydantic import BaseModel, Field
from dotenv import load_dotenv

load_dotenv()

from app.agent import build_agent, MockAgentExecutor
from app.chains import (
    build_task_analysis_chain,
    build_qa_chain,
    build_summarize_chain
)
from app.memory_store import memory_store


# ─── Global Services ─────────────────────────────────────────

_agent = None
_analysis_chain = None
_qa_chain = None
_summarize_chain = None


@asynccontextmanager
async def lifespan(app: FastAPI):
    global _agent, _analysis_chain, _qa_chain, _summarize_chain

    print("\n" + "=" * 60)
    print("  LangChain Task Management Agent")
    print("  Day 33 — Agents, Tools, Memory & Chains")
    print("=" * 60)

    print("\n  Initializing LangChain components...")

    # Build agent
    _agent = build_agent()
    is_mock = isinstance(_agent, MockAgentExecutor)
    print(f"  ✅ Agent: {'Mock (no API key)' if is_mock else 'Real (Claude)'}")

    # Build chains
    _analysis_chain = build_task_analysis_chain()
    _qa_chain = build_qa_chain()
    _summarize_chain = build_summarize_chain()
    print(f"  ✅ Chains: task analysis, Q&A, summarization")

    # Init vector store
    from tools.kb_tools import get_vectorstore
    vs = get_vectorstore()
    if vs:
        print(f"  ✅ Knowledge base: vector store loaded")
    else:
        print(f"  ✅ Knowledge base: keyword fallback")

    print(f"\n  Docs: http://localhost:8000/docs\n")
    yield
    print("\n  Sessions:", len(memory_store.list_sessions()))
    print("  Shutting down...")


# ─── App ─────────────────────────────────────────────────────

app = FastAPI(
    title="LangChain Task Management Agent",
    description="""
## 🤖 LangChain AI Agent — Day 33

An autonomous agent that manages tasks, searches documentation,
and answers questions using LangChain tools and memory.

### Agent Capabilities
The agent can:
- 📋 **List, create, and complete tasks**
- ⚠️ **Find overdue tasks** and prioritize them
- 🔍 **Search knowledge base** for debugging/configuration help
- 📊 **Generate reports** for standup meetings
- 🧠 **Remember conversation context** across turns

### Architecture