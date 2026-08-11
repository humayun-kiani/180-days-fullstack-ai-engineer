# ============================================================
# app/main.py
# Task Knowledge Base — Semantic Search & RAG API
# Day 31 — Embeddings, Vector Databases & Semantic Search
# ============================================================

import time
from contextlib import asynccontextmanager
from datetime import datetime
from typing import Optional

from fastapi import FastAPI, HTTPException, Query
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field

from app.knowledge_base import (
    build_knowledge_base, load_knowledge_base,
    get_chroma_client, COLLECTION_NAME
)
from app.search import (
    semantic_search, keyword_search, compare_search_methods
)
from app.rag import rag_pipeline
from data.articles import ARTICLES


# ─── Global state ────────────────────────────────────────────

_collection = None
_kb_stats = {}


def get_collection():
    global _collection
    if _collection is None:
        raise HTTPException(503, "Knowledge base not initialized")
    return _collection


# ─── Startup ─────────────────────────────────────────────────

@asynccontextmanager
async def lifespan(app: FastAPI):
    global _collection, _kb_stats

    print("\n" + "=" * 60)
    print("  Task Knowledge Base — Semantic Search & RAG")
    print("  Day 31 — Embeddings & Vector Databases")
    print("=" * 60)

    print("\n  Initializing knowledge base...")
    start = time.time()

    # Try loading existing KB, build if not found
    _collection = load_knowledge_base(persist=True)

    if _collection is None:
        print("  No existing knowledge base found. Building...")
        _collection, _kb_stats = build_knowledge_base(
            ARTICLES,
            chunk_size=200,
            overlap=40,
            persist=True
        )
    else:
        _kb_stats = {
            "articles": len(ARTICLES),
            "total_chunks": _collection.count()
        }

    elapsed = time.time() - start
    print(f"\n  ✅ Ready in {elapsed:.1f}s")
    print(f"  Docs:   http://localhost:8000/docs")
    print(f"  Demo:   http://localhost:8000/demo\n")

    yield

    print("\n  Shutting down...")


# ─── App ─────────────────────────────────────────────────────

app = FastAPI(
    title="Task Knowledge Base API",
    description="""
## 📚 Semantic Knowledge Base with RAG

A ChromaDB-powered knowledge base that finds articles by **meaning**, not keywords.

### Endpoints
- `GET /search` — Semantic search by meaning
- `GET /search/compare` — Side-by-side: semantic vs keyword
- `POST /rag` — Retrieval-Augmented Generation (Q&A)
- `GET /articles` — List all knowledge base articles
- `GET /demo` — Try example queries

### Day 31 — Embeddings, Vector Databases & Semantic Search
    """,
    version="1.0.0",
    lifespan=lifespan
)


# ─── Search Endpoints ────────────────────────────────────────

@app.get(
    "/search",
    summary="Semantic search",
    description="Find knowledge base articles by meaning, not keywords."
)
def search(
    q: str = Query(
        ...,
        min_length=3,
        description="Search query",
        example="my api is returning errors"
    ),
    n: int = Query(3, ge=1, le=10, description="Number of results"),
    category: Optional[str] = Query(
        None,
        description="Filter by category",
        example="debugging"
    )
):
    """Semantic search over the knowledge base."""
    collection = get_collection()
    start = time.perf_counter()

    results = semantic_search(collection, q, n_results=n, category_filter=category)

    elapsed_ms = (time.perf_counter() - start) * 1000

    return {
        "query": q,
        "results": [
            {
                "rank": i + 1,
                "article_id": r.article_id,
                "title": r.article_title,
                "category": r.category,
                "relevance_score": r.score,
                "tags": r.tags,
                "preview": r.chunk_text[:200] + (
                    "..." if len(r.chunk_text) > 200 else ""
                )
            }
            for i, r in enumerate(results)
        ],
        "total_found": len(results),
        "search_type": "semantic",
        "latency_ms": round(elapsed_ms, 1),
        "knowledge_base_size": _kb_stats.get("total_chunks", 0)
    }


@app.get(
    "/search/compare",
    summary="Compare semantic vs keyword search",
    description="See how semantic search finds what keyword search misses."
)
def compare_search(
    q: str = Query(
        ...,
        description="Search query",
        example="database is unresponsive"
    ),
    n: int = Query(3, ge=1, le=5)
):
    """Side-by-side comparison of semantic and keyword search."""
    collection = get_collection()
    return compare_search_methods(collection, ARTICLES, q, n_results=n)


# ─── RAG Endpoint ────────────────────────────────────────────

class RAGRequest(BaseModel):
    question: str = Field(
        min_length=5,
        max_length=500,
        example="How do I fix JWT token expiration errors?"
    )
    n_results: int = Field(default=3, ge=1, le=5)
    min_score: float = Field(default=0.2, ge=0.0, le=1.0)


@app.post(
    "/rag",
    summary="Retrieval-Augmented Generation",
    description="""
Ask a question — the system retrieves relevant knowledge base articles
and uses them to generate a grounded answer.

In production: replace the template answer with an LLM call
(Claude, GPT-4, etc.) using the retrieved context.
    """
)
def rag_endpoint(request: RAGRequest):
    """RAG: retrieve context + generate answer."""
    collection = get_collection()
    start = time.perf_counter()

    result = rag_pipeline(
        collection=collection,
        question=request.question,
        n_results=request.n_results,
        min_score=request.min_score
    )

    result["latency_ms"] = round((time.perf_counter() - start) * 1000, 1)
    return result


# ─── Knowledge Base Endpoints ─────────────────────────────────

@app.get("/articles", summary="List all articles")
def list_articles(
    category: Optional[str] = Query(None, description="Filter by category")
):
    """List all articles in the knowledge base."""
    articles = ARTICLES
    if category:
        articles = [a for a in articles if a.get("category") == category]

    categories = list(set(a.get("category", "general") for a in ARTICLES))

    return {
        "articles": [
            {
                "id": a["id"],
                "title": a["title"],
                "category": a.get("category", "general"),
                "tags": a.get("tags", []),
                "preview": a["content"][:100] + "..."
            }
            for a in articles
        ],
        "total": len(articles),
        "categories": sorted(categories)
    }


@app.get("/articles/{article_id}", summary="Get article by ID")
def get_article(article_id: str):
    """Get a specific article by ID."""
    article = next((a for a in ARTICLES if a["id"] == article_id), None)
    if not article:
        raise HTTPException(404, f"Article '{article_id}' not found")
    return article


@app.post("/rebuild", summary="Rebuild knowledge base")
def rebuild_knowledge_base():
    """Rebuild the knowledge base from scratch."""
    global _collection, _kb_stats
    _collection, _kb_stats = build_knowledge_base(
        ARTICLES, chunk_size=200, overlap=40, persist=True
    )
    return {
        "message": "Knowledge base rebuilt",
        "stats": _kb_stats
    }


# ─── Demo Endpoint ────────────────────────────────────────────

@app.get("/demo", summary="Demo — example queries")
def demo():
    """Run several demo queries to show semantic search in action."""
    collection = get_collection()

    demo_queries = [
        ("my API is throwing 500 errors", "→ Should find debugging article"),
        ("token keeps expiring", "→ Should find JWT auth article (no 'JWT' in query!)"),
        ("container keeps dying", "→ Should find Docker health check article"),
        ("DB is unresponsive", "→ Should find PostgreSQL/Redis articles"),
        ("tests are failing randomly", "→ Should find testing best practices"),
    ]

    demo_results = []
    for query, note in demo_queries:
        results = semantic_search(collection, query, n_results=2)
        demo_results.append({
            "query": query,
            "note": note,
            "top_result": {
                "title": results[0].article_title if results else "No results",
                "score": results[0].score if results else 0,
                "category": results[0].category if results else ""
            }
        })

    return {
        "message": "Semantic search demo — finding articles by MEANING",
        "demos": demo_results,
        "key_insight": (
            "Notice: 'token keeps expiring' finds the JWT article "
            "even though neither 'JWT' nor 'expires' appear in the query. "
            "Semantic search understands the MEANING, not just keywords."
        )
    }


# ─── System Endpoints ─────────────────────────────────────────

@app.get("/health")
def health():
    return {
        "status": "healthy",
        "knowledge_base": {
            "articles": _kb_stats.get("articles", 0),
            "chunks": _kb_stats.get("total_chunks", 0)
        },
        "timestamp": datetime.utcnow().isoformat(),
        "day": "Day 31 — Embeddings, Vector Databases & Semantic Search"
    }


@app.get("/")
def root():
    return {
        "name": "Task Knowledge Base API",
        "day": "Day 31 — Embeddings & Semantic Search",
        "docs": "/docs",
        "demo": "/demo",
        "endpoints": {
            "semantic_search": "GET /search?q=your+query",
            "comparison": "GET /search/compare?q=your+query",
            "rag": "POST /rag",
            "articles": "GET /articles"
        }
    }