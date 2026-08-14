# ============================================================
# app/rag_pipeline.py
# Complete RAG pipeline: retrieve context → build prompt → generate
# ============================================================

import chromadb
from pathlib import Path
from typing import Optional

from app.claude_client import ClaudeClient

CHROMA_DIR = Path(__file__).parent.parent / "chroma_db"
COLLECTION_NAME = "task_knowledge_base"

# System prompt for the RAG chatbot
RAG_SYSTEM_PROMPT = """You are a helpful technical assistant for a software development team
using a task management system called TaskManager.

Your role:
- Answer questions about debugging, authentication, performance, database, and DevOps
- Give specific, actionable advice — not generic platitudes
- Refer to the provided documentation context when available
- Use code examples when helpful
- Be concise — developers are busy

When context is provided from the knowledge base:
- Ground your answer in that specific documentation
- Cite which article/guide your answer comes from
- If the context doesn't fully answer the question, say so and provide what you can

When no context is available:
- Provide general best-practice advice
- Clearly indicate you're answering from general knowledge, not specific docs

Format:
- Use markdown for code blocks, bullet points, and emphasis
- Keep responses focused and under 400 words unless detail is specifically needed"""


class RAGPipeline:
    """
    Retrieval-Augmented Generation pipeline.

    Combines ChromaDB semantic retrieval with Claude generation
    to answer questions grounded in the knowledge base.
    """

    def __init__(
        self,
        claude_client: ClaudeClient,
        n_results: int = 3,
        min_relevance_score: float = 0.3,
        persist_kb: bool = True
    ):
        self.claude = claude_client
        self.n_results = n_results
        self.min_score = min_relevance_score

        # Load or build ChromaDB
        self._collection = self._load_collection(persist_kb)

    def _load_collection(self, persist: bool) -> Optional[object]:
        """Load ChromaDB collection if it exists."""
        try:
            if persist:
                client = chromadb.PersistentClient(path=str(CHROMA_DIR))
            else:
                client = chromadb.Client()

            collection = client.get_collection(COLLECTION_NAME)
            count = collection.count()
            print(f"  ✅ Knowledge base loaded: {count} chunks")
            return collection

        except Exception:
            print("  ⚠️  Knowledge base not found. Build it by running Day 31 first.")
            print("       Continuing without retrieval (direct Claude answers only)")
            return None

    def retrieve(self, query: str) -> tuple[list[dict], str]:
        """
        Retrieve relevant context for a query.

        Returns:
            tuple: (sources list, formatted context string)
        """
        if not self._collection:
            return [], ""

        try:
            results = self._collection.query(
                query_texts=[query],
                n_results=min(self.n_results, self._collection.count()),
                include=["documents", "metadatas", "distances"]
            )
        except Exception as e:
            print(f"  Retrieval error: {e}")
            return [], ""

        if not results["documents"] or not results["documents"][0]:
            return [], ""

        sources = []
        context_parts = []
        seen_articles = set()

        for doc, meta, distance in zip(
            results["documents"][0],
            results["metadatas"][0],
            results["distances"][0]
        ):
            similarity = max(0.0, 1.0 - float(distance))

            if similarity < self.min_score:
                continue

            article_id = meta.get("article_id", "")
            if article_id in seen_articles:
                continue
            seen_articles.add(article_id)

            title = meta.get("article_title", "Unknown")
            category = meta.get("category", "")

            sources.append({
                "article_id": article_id,
                "title": title,
                "category": category,
                "relevance_score": round(similarity, 3),
                "preview": doc[:100] + "..."
            })
            context_parts.append(f"[{title}]\n{doc}")

        context = "\n\n---\n\n".join(context_parts) if context_parts else ""
        return sources, context

    def build_rag_prompt(
        self,
        question: str,
        context: str
    ) -> str:
        """Build the RAG prompt with retrieved context."""
        if context:
            return f"""RELEVANT DOCUMENTATION FROM KNOWLEDGE BASE:
{context}

---

Based on the documentation above, please answer this question:
{question}

If the documentation doesn't fully answer the question, supplement with general knowledge
and clearly indicate which parts come from the docs vs general knowledge."""
        else:
            return question

    def answer(
        self,
        question: str,
        conversation_messages: list[dict],
        use_kb: bool = True,
        max_tokens: int = 1024,
        temperature: float = 0.5
    ) -> tuple[str, list[dict], dict]:
        """
        Answer a question using RAG pipeline.

        Args:
            question: The user's question.
            conversation_messages: Prior conversation history.
            use_kb: Whether to use knowledge base retrieval.
            max_tokens: Max tokens for response.
            temperature: Response randomness.

        Returns:
            tuple: (answer text, sources, usage stats)
        """
        # Step 1: Retrieve
        sources = []
        context = ""
        if use_kb:
            sources, context = self.retrieve(question)

        # Step 2: Build prompt
        prompt = self.build_rag_prompt(question, context)

        # Step 3: Build messages (conversation history + new question)
        messages = conversation_messages.copy()

        # Replace last user message with RAG-enriched version
        if messages and messages[-1]["role"] == "user":
            messages[-1] = {"role": "user", "content": prompt}
        else:
            messages.append({"role": "user", "content": prompt})

        # Step 4: Generate
        answer, usage = self.claude.complete(
            messages=messages,
            system=RAG_SYSTEM_PROMPT,
            max_tokens=max_tokens,
            temperature=temperature
        )

        usage["retrieved_chunks"] = len(sources)
        usage["context_words"] = len(context.split()) if context else 0

        return answer, sources, usage

    def stream_answer(
        self,
        question: str,
        conversation_messages: list[dict],
        use_kb: bool = True
    ):
        """
        Stream the answer token by token.

        Yields:
            str: Individual text tokens.
        """
        sources, context = self.retrieve(question) if use_kb else ([], "")
        prompt = self.build_rag_prompt(question, context)

        messages = conversation_messages.copy()
        if messages and messages[-1]["role"] == "user":
            messages[-1] = {"role": "user", "content": prompt}
        else:
            messages.append({"role": "user", "content": prompt})

        yield from self.claude.stream(
            messages=messages,
            system=RAG_SYSTEM_PROMPT
        )