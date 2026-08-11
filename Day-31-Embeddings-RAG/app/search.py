# ============================================================
# app/search.py
# Semantic search and keyword search implementations
# ============================================================

import re
from dataclasses import dataclass, field


@dataclass
class SearchResult:
    """A single search result."""
    article_id: str
    article_title: str
    category: str
    chunk_text: str
    score: float
    chunk_index: int
    tags: list[str] = field(default_factory=list)
    search_type: str = "semantic"


def semantic_search(
    collection,
    query: str,
    n_results: int = 5,
    category_filter: str | None = None
) -> list[SearchResult]:
    """
    Search the knowledge base by meaning using vector similarity.

    Args:
        collection: ChromaDB collection.
        query: Search query text.
        n_results: Number of results to return.
        category_filter: Optional category to filter results.

    Returns:
        list[SearchResult]: Ranked search results.
    """
    where_filter = None
    if category_filter:
        where_filter = {"category": category_filter}

    try:
        results = collection.query(
            query_texts=[query],
            n_results=min(n_results, collection.count()),
            where=where_filter,
            include=["documents", "metadatas", "distances"]
        )
    except Exception as e:
        return []

    if not results["documents"] or not results["documents"][0]:
        return []

    search_results = []
    for doc, meta, distance in zip(
        results["documents"][0],
        results["metadatas"][0],
        results["distances"][0]
    ):
        # ChromaDB returns distance (lower = more similar)
        # Convert to similarity score (higher = more similar)
        # For cosine distance: similarity = 1 - distance
        similarity = max(0.0, 1.0 - float(distance))

        tags = meta.get("tags", "").split(",") if meta.get("tags") else []
        tags = [t.strip() for t in tags if t.strip()]

        search_results.append(SearchResult(
            article_id=meta.get("article_id", ""),
            article_title=meta.get("article_title", ""),
            category=meta.get("category", ""),
            chunk_text=doc,
            score=round(similarity, 4),
            chunk_index=meta.get("chunk_index", 0),
            tags=tags,
            search_type="semantic"
        ))

    return sorted(search_results, key=lambda r: r.score, reverse=True)


def keyword_search(
    articles: list[dict],
    query: str,
    n_results: int = 5
) -> list[SearchResult]:
    """
    Traditional keyword search using TF-IDF-like scoring.

    Included for comparison with semantic search.

    Args:
        articles: List of article dicts.
        query: Search query.
        n_results: Max results to return.

    Returns:
        list[SearchResult]: Ranked search results.
    """
    query_words = set(query.lower().split())
    scored = []

    for article in articles:
        content = f"{article['title']} {article['content']}".lower()
        content_words = set(content.split())

        # Simple overlap scoring
        exact_phrase = query.lower() in content
        word_overlap = len(query_words & content_words)
        title_match = sum(
            1 for w in query_words if w in article["title"].lower()
        )

        score = (
            word_overlap * 0.5 +
            title_match * 2.0 +
            (3.0 if exact_phrase else 0)
        )

        if score > 0:
            # Normalize by query length
            score = score / max(len(query_words), 1)

            scored.append(SearchResult(
                article_id=article["id"],
                article_title=article["title"],
                category=article.get("category", ""),
                chunk_text=article["content"][:300] + "...",
                score=round(score, 4),
                chunk_index=0,
                tags=article.get("tags", []),
                search_type="keyword"
            ))

    return sorted(scored, key=lambda r: r.score, reverse=True)[:n_results]


def compare_search_methods(
    collection,
    articles: list[dict],
    query: str,
    n_results: int = 3
) -> dict:
    """
    Compare semantic vs keyword search for a given query.

    Args:
        collection: ChromaDB collection.
        articles: Original articles (for keyword search).
        query: Search query.
        n_results: Results per method.

    Returns:
        dict: Comparison results.
    """
    semantic_results = semantic_search(collection, query, n_results)
    keyword_results = keyword_search(articles, query, n_results)

    # Find what semantic found that keyword missed
    semantic_ids = {r.article_id for r in semantic_results}
    keyword_ids = {r.article_id for r in keyword_results}

    only_semantic = semantic_ids - keyword_ids
    only_keyword = keyword_ids - semantic_ids
    both = semantic_ids & keyword_ids

    return {
        "query": query,
        "semantic_results": [
            {
                "title": r.article_title,
                "score": r.score,
                "category": r.category,
                "preview": r.chunk_text[:120] + "..."
            }
            for r in semantic_results
        ],
        "keyword_results": [
            {
                "title": r.article_title,
                "score": r.score,
                "category": r.category,
                "preview": r.chunk_text[:120] + "..."
            }
            for r in keyword_results
        ],
        "overlap_analysis": {
            "found_by_both": list(both),
            "only_semantic": list(only_semantic),
            "only_keyword": list(only_keyword),
            "semantic_advantage": len(only_semantic),
            "keyword_advantage": len(only_keyword)
        }
    }