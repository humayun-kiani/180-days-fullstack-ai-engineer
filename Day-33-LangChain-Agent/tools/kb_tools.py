# ============================================================
# tools/kb_tools.py
# Knowledge base search tool for the agent
# ============================================================

import os
from pathlib import Path
from langchain_core.tools import tool
from langchain_community.vectorstores import Chroma

# Try to use HuggingFace embeddings (free, local)
try:
    from langchain_huggingface import HuggingFaceEmbeddings
    _embeddings = HuggingFaceEmbeddings(model_name="all-MiniLM-L6-v2")
    EMBEDDINGS_AVAILABLE = True
except Exception:
    EMBEDDINGS_AVAILABLE = False

CHROMA_DIR = Path(__file__).parent.parent / "chroma_db"
_vectorstore = None


def get_vectorstore():
    """Load or build the ChromaDB vector store."""
    global _vectorstore

    if _vectorstore is not None:
        return _vectorstore

    if not EMBEDDINGS_AVAILABLE:
        return None

    if CHROMA_DIR.exists():
        try:
            _vectorstore = Chroma(
                persist_directory=str(CHROMA_DIR),
                embedding_function=_embeddings,
                collection_name="task_knowledge_base"
            )
            return _vectorstore
        except Exception:
            pass

    # Build from documents
    from app.documents import load_documents, split_documents
    docs = load_documents()
    chunks = split_documents(docs)

    _vectorstore = Chroma.from_documents(
        documents=chunks,
        embedding=_embeddings,
        persist_directory=str(CHROMA_DIR),
        collection_name="task_knowledge_base"
    )
    print(f"  ✅ Vector store built with {len(chunks)} chunks")
    return _vectorstore


def _simple_keyword_search(query: str) -> str:
    """Fallback keyword search when embeddings not available."""
    from app.documents import KB_ARTICLES
    query_words = set(query.lower().split())
    scored = []
    for article in KB_ARTICLES:
        text = f"{article['title']} {article['content']}".lower()
        score = sum(1 for w in query_words if w in text)
        if score > 0:
            scored.append((score, article))
    scored.sort(reverse=True)
    if not scored:
        return "No relevant articles found."
    top = scored[:2]
    return "\n\n---\n\n".join(
        f"[{a['title']}]\n{a['content'][:400]}" for _, a in top
    )


@tool
def search_knowledge_base(query: str) -> str:
    """
    Search the task management knowledge base for relevant documentation.

    Use this tool when the user asks about:
    - Debugging errors (500, 401, 404, JWT issues)
    - Performance optimization (slow API, database queries)
    - Database configuration (PostgreSQL, connection pools)
    - Caching (Redis patterns, TTL)
    - Docker and deployment
    - Celery background tasks
    - Testing FastAPI applications

    Args:
        query: Natural language search query

    Returns:
        Relevant documentation excerpts from the knowledge base
    """
    vs = get_vectorstore()

    if vs is None:
        return _simple_keyword_search(query)

    try:
        docs = vs.similarity_search(query, k=3)
        if not docs:
            return "No relevant documentation found."
        parts = []
        for doc in docs:
            title = doc.metadata.get("title", "")
            category = doc.metadata.get("category", "")
            parts.append(f"[Source: {title} | Category: {category}]\n{doc.page_content}")
        return "\n\n---\n\n".join(parts)
    except Exception as e:
        return _simple_keyword_search(query)