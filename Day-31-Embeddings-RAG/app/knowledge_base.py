# ============================================================
# app/knowledge_base.py
# Build and manage the ChromaDB knowledge base
# ============================================================

import chromadb
from chromadb.config import Settings as ChromaSettings
from pathlib import Path
from typing import Optional

from app.embedder import chunk_text, get_embedder


CHROMA_DIR = Path(__file__).parent.parent / "chroma_db"
COLLECTION_NAME = "task_knowledge_base"


def get_chroma_client(persist: bool = True) -> chromadb.ClientAPI:
    """Get ChromaDB client (persistent or in-memory)."""
    if persist:
        return chromadb.PersistentClient(path=str(CHROMA_DIR))
    return chromadb.Client()


def get_or_create_collection(
    client: chromadb.ClientAPI,
    name: str = COLLECTION_NAME
) -> chromadb.Collection:
    """Get existing collection or create a new one."""
    try:
        return client.get_collection(name)
    except Exception:
        return client.create_collection(
            name=name,
            metadata={"hnsw:space": "cosine"}
        )


def build_knowledge_base(
    articles: list[dict],
    chunk_size: int = 200,
    overlap: int = 40,
    persist: bool = True
) -> tuple[chromadb.Collection, dict]:
    """
    Build the vector knowledge base from articles.

    For each article:
    1. Split into overlapping chunks
    2. Generate embeddings for each chunk
    3. Store in ChromaDB with metadata

    Args:
        articles: List of article dicts with id, title, content, tags.
        chunk_size: Words per chunk.
        overlap: Words to overlap between chunks.
        persist: Whether to persist to disk.

    Returns:
        tuple: (ChromaDB collection, stats dict)
    """
    client = get_chroma_client(persist=persist)

    # Delete existing collection if rebuilding
    try:
        client.delete_collection(COLLECTION_NAME)
    except Exception:
        pass

    collection = client.create_collection(
        name=COLLECTION_NAME,
        metadata={"hnsw:space": "cosine"}
    )

    embedder = get_embedder()
    total_chunks = 0
    doc_ids = []
    documents = []
    metadatas = []

    print(f"\n  Building knowledge base from {len(articles)} articles...")

    for article in articles:
        # Create chunks
        full_text = f"{article['title']}. {article['content']}"
        chunks = chunk_text(full_text, chunk_size=chunk_size, overlap=overlap)

        for chunk_idx, chunk in enumerate(chunks):
            doc_id = f"{article['id']}_chunk_{chunk_idx}"
            doc_ids.append(doc_id)
            documents.append(chunk)
            metadatas.append({
                "article_id": article["id"],
                "article_title": article["title"],
                "category": article.get("category", "general"),
                "tags": ",".join(article.get("tags", [])),
                "chunk_index": chunk_idx,
                "total_chunks": len(chunks)
            })
            total_chunks += 1

    # Add all documents (ChromaDB generates embeddings if no embedding_function provided)
    # We let ChromaDB use its default embedding model for simplicity
    # In production you'd pass your own embedding function
    collection.add(
        documents=documents,
        metadatas=metadatas,
        ids=doc_ids
    )

    stats = {
        "articles": len(articles),
        "total_chunks": total_chunks,
        "avg_chunks_per_article": total_chunks / len(articles),
        "collection_name": COLLECTION_NAME
    }

    print(f"  ✅ Knowledge base built:")
    print(f"     Articles:      {stats['articles']}")
    print(f"     Total chunks:  {stats['total_chunks']}")
    print(f"     Avg per article: {stats['avg_chunks_per_article']:.1f}")

    return collection, stats


def load_knowledge_base(persist: bool = True) -> Optional[chromadb.Collection]:
    """Load existing knowledge base from disk."""
    client = get_chroma_client(persist=persist)
    try:
        collection = client.get_collection(COLLECTION_NAME)
        count = collection.count()
        print(f"  ✅ Loaded knowledge base: {count} chunks")
        return collection
    except Exception:
        return None