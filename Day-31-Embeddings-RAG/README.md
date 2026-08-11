# Day 31 — Embeddings, Vector Databases & Semantic Search

> **Phase 3 — AI & Machine Learning** | Week 6 | Day 31 of 180

---

## 📌 What I Learned Today

- What embeddings are: text → dense numeric vectors where meaning = proximity
- Why embeddings beat TF-IDF: "automobile" ≈ "car", not just character matching
- Word2Vec → BERT → sentence-transformers evolution
- Cosine similarity: measures angle between vectors (direction = meaning)
- Why cosine, not Euclidean: captures directional similarity regardless of magnitude
- sentence-transformers library: pre-trained models for sentence-level embeddings
- all-MiniLM-L6-v2: 384-dim, fast, great quality/speed balance
- model.encode(): text → np.ndarray of shape (384,)
- ChromaDB: embedded vector database, no server required
- chromadb.Client() vs chromadb.PersistentClient(path): in-memory vs disk
- collection.add(documents, ids, metadatas): store text + metadata
- collection.query(query_texts, n_results): find semantically similar docs
- ChromaDB returns distances (not similarities): similarity = 1 - distance
- Document chunking: split long texts into overlapping windows
- chunk_size and overlap: balance context vs granularity
- Why overlap: avoid losing context at chunk boundaries
- RAG pattern: Retrieve → Augment → Generate
- Semantic search vs keyword search: semantic finds meaning, not just words
- "token keeps expiring" finds JWT article with no keyword overlap!
- Vector database indexing: HNSW algorithm for approximate nearest neighbors
- Metadata filtering: filter by category alongside semantic search
- get_or_create_collection + PersistentClient: KB persists across restarts
- Template-based RAG: retrieve context → fill answer template
- In production RAG: retrieved context goes into LLM prompt

## 🔨 Project Built

**Task Knowledge Base** — Full semantic search system:

- 12 knowledge base articles covering debugging, auth, performance,
  database, Docker, Celery, Redis, Nginx, testing, WebSockets, Git, logging
- Embedder: sentence-transformers with TF-IDF fallback
- chunk_text(): overlapping chunking with configurable size and overlap
- build_knowledge_base(): chunk → embed → store in ChromaDB
- PersistentClient: KB survives application restarts
- semantic_search(): ChromaDB vector search with metadata filtering
- keyword_search(): TF-IDF-like baseline for comparison
- compare_search_methods(): side-by-side comparison with overlap analysis
- rag_pipeline(): retrieve_context → template_answer
- FastAPI: GET /search, GET /search/compare, POST /rag,
  GET /articles, GET /demo, POST /rebuild

## 🚀 How to Run

```bash
cd Day-31-Embeddings-RAG
python -m venv venv && source venv/bin/activate
pip install -r requirements.txt

uvicorn app.main:app --reload

# First run downloads embedding model and builds KB (~30s)
# Subsequent runs load from disk (<1s)

# Open: http://localhost:8000/docs
# Try: http://localhost:8000/demo
```

## 🧠 Key Concept: Semantic vs Keyword Search

| Query                      | Keyword Finds                  | Semantic Finds          |
| -------------------------- | ------------------------------ | ----------------------- |
| "token keeps expiring"     | Nothing (no "JWT" or "expire") | JWT Token article       |
| "DB is unresponsive"       | Nothing (no "PostgreSQL")      | Connection Pool article |
| "container keeps dying"    | Nothing (no "Docker")          | Docker health check     |
| "API returning 500 errors" | ✅ Debugging article           | ✅ Debugging article    |

## 🔗 Back to Main Roadmap

[← Back to 180-Day Roadmap](../README.md)
