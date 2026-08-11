# ============================================================
# app/rag.py
# Retrieval-Augmented Generation (without external LLM)
# Uses template-based answer generation from retrieved context
# ============================================================

from app.search import semantic_search, SearchResult


def retrieve_context(
    collection,
    question: str,
    n_results: int = 3,
    min_score: float = 0.2
) -> tuple[list[SearchResult], str]:
    """
    Retrieve relevant context for a question.

    Args:
        collection: ChromaDB collection.
        question: User's question.
        n_results: Max chunks to retrieve.
        min_score: Minimum similarity threshold.

    Returns:
        tuple: (relevant_results, formatted_context_string)
    """
    results = semantic_search(collection, question, n_results=n_results)

    # Filter by minimum score
    relevant = [r for r in results if r.score >= min_score]

    if not relevant:
        return [], ""

    # Format context for answer generation
    context_parts = []
    seen_articles = set()

    for result in relevant:
        # Deduplicate by article (prefer highest-scoring chunk)
        if result.article_id in seen_articles:
            continue
        seen_articles.add(result.article_id)

        context_parts.append(
            f"[Source: {result.article_title}]\n{result.chunk_text}"
        )

    context = "\n\n---\n\n".join(context_parts)
    return relevant, context


def template_answer(
    question: str,
    context: str,
    results: list[SearchResult]
) -> str:
    """
    Generate a template-based answer from retrieved context.

    In production: replace this with an LLM call using the context.

    Args:
        question: User's question.
        context: Retrieved context text.
        results: SearchResult objects (for metadata).

    Returns:
        str: Generated answer.
    """
    if not results:
        return (
            "I couldn't find relevant information in the knowledge base "
            f"for your question: '{question}'. Try rephrasing or checking "
            "if this topic is covered in our documentation."
        )

    # Extract the most relevant chunk
    best = results[0]
    confidence = "high" if best.score > 0.6 else "medium" if best.score > 0.4 else "low"

    sources = [r.article_title for r in results[:3]]
    source_list = ", ".join(f"'{s}'" for s in sources)

    answer = f"""Based on the knowledge base (confidence: {confidence}):

{best.chunk_text[:500]}{"..." if len(best.chunk_text) > 500 else ""}

Sources consulted: {source_list}

[Note: In production, this context would be sent to an LLM (Claude, GPT-4, etc.)
to generate a natural language answer. The retrieval step here is the key
innovation — finding the right context is 80% of the work.]"""

    return answer


def rag_pipeline(
    collection,
    question: str,
    n_results: int = 3,
    min_score: float = 0.2
) -> dict:
    """
    Complete RAG pipeline: question → retrieve → generate.

    Args:
        collection: ChromaDB collection.
        question: User's question.
        n_results: Max context chunks.
        min_score: Minimum relevance threshold.

    Returns:
        dict: Complete RAG result with answer, sources, scores.
    """
    # Step 1: Retrieve
    results, context = retrieve_context(
        collection, question, n_results, min_score
    )

    # Step 2: Generate (template-based for now)
    answer = template_answer(question, context, results)

    # Step 3: Package result
    return {
        "question": question,
        "answer": answer,
        "sources": [
            {
                "article_id": r.article_id,
                "title": r.article_title,
                "category": r.category,
                "relevance_score": r.score,
                "preview": r.chunk_text[:150] + "..."
            }
            for r in results[:3]
        ],
        "context_retrieved": len(results) > 0,
        "retrieval_confidence": results[0].score if results else 0.0,
        "rag_pattern": {
            "step_1_retrieve": f"Found {len(results)} relevant chunks",
            "step_2_augment": f"Context: {len(context.split())} words",
            "step_3_generate": "Template answer (replace with LLM in production)"
        }
    }