# ============================================================
# app/embedder.py
# Text embedding using sentence-transformers
# ============================================================

import numpy as np
from typing import Union
from functools import lru_cache

try:
    from sentence_transformers import SentenceTransformer
    SENTENCE_TRANSFORMERS_AVAILABLE = True
except ImportError:
    SENTENCE_TRANSFORMERS_AVAILABLE = False


class SimpleEmbedder:
    """
    Fallback embedder using TF-IDF when sentence-transformers unavailable.
    Lower quality but zero additional dependencies.
    """

    def __init__(self):
        from sklearn.feature_extraction.text import TfidfVectorizer
        self.vectorizer = TfidfVectorizer(
            max_features=512,
            ngram_range=(1, 2),
            sublinear_tf=True
        )
        self._fitted = False
        self._corpus: list[str] = []

    def fit(self, texts: list[str]) -> None:
        self.vectorizer.fit(texts)
        self._fitted = True

    def encode(
        self,
        texts: Union[str, list[str]],
        show_progress_bar: bool = False
    ) -> np.ndarray:
        if isinstance(texts, str):
            texts = [texts]
        if not self._fitted:
            self.vectorizer.fit(texts)
            self._fitted = True
        return self.vectorizer.transform(texts).toarray().astype(np.float32)

    @property
    def embedding_dim(self) -> int:
        return 512


class Embedder:
    """
    Text embedding wrapper.

    Uses sentence-transformers if available, falls back to TF-IDF.
    The interface is the same regardless of which backend is used.
    """

    def __init__(self, model_name: str = "all-MiniLM-L6-v2"):
        self.model_name = model_name

        if SENTENCE_TRANSFORMERS_AVAILABLE:
            print(f"  Loading embedding model: {model_name}")
            self._model = SentenceTransformer(model_name)
            self._backend = "sentence-transformers"
            print(f"  ✅ Embedding model ready ({self.embedding_dim} dimensions)")
        else:
            print("  ⚠️  sentence-transformers not available, using TF-IDF fallback")
            self._model = SimpleEmbedder()
            self._backend = "tfidf-fallback"

    def encode(
        self,
        texts: Union[str, list[str]],
        show_progress_bar: bool = False,
        batch_size: int = 32
    ) -> np.ndarray:
        """
        Encode text(s) into embedding vector(s).

        Args:
            texts: A single string or list of strings.
            show_progress_bar: Show progress for large batches.
            batch_size: Process in batches (for large inputs).

        Returns:
            np.ndarray: Shape (n, dim) for list, (dim,) for single string.
        """
        if isinstance(texts, str):
            single = True
            texts = [texts]
        else:
            single = False

        if self._backend == "sentence-transformers":
            embeddings = self._model.encode(
                texts,
                show_progress_bar=show_progress_bar,
                batch_size=batch_size
            )
        else:
            embeddings = self._model.encode(texts)

        return embeddings[0] if single else embeddings

    @property
    def embedding_dim(self) -> int:
        if self._backend == "sentence-transformers":
            return self._model.get_sentence_embedding_dimension()
        return 512

    @property
    def backend(self) -> str:
        return self._backend


def cosine_similarity(vec_a: np.ndarray, vec_b: np.ndarray) -> float:
    """Compute cosine similarity between two vectors."""
    norm_a = np.linalg.norm(vec_a)
    norm_b = np.linalg.norm(vec_b)
    if norm_a == 0 or norm_b == 0:
        return 0.0
    return float(np.dot(vec_a, vec_b) / (norm_a * norm_b))


def cosine_similarity_batch(
    query_vec: np.ndarray,
    matrix: np.ndarray
) -> np.ndarray:
    """
    Compute cosine similarity between a query and all rows in a matrix.

    Args:
        query_vec: Query embedding of shape (dim,).
        matrix: Matrix of embeddings, shape (n, dim).

    Returns:
        np.ndarray: Similarity scores, shape (n,).
    """
    norms = np.linalg.norm(matrix, axis=1)
    query_norm = np.linalg.norm(query_vec)

    if query_norm == 0:
        return np.zeros(len(matrix))

    # Avoid division by zero
    norms = np.where(norms == 0, 1e-8, norms)

    return matrix @ query_vec / (norms * query_norm)


def chunk_text(
    text: str,
    chunk_size: int = 200,
    overlap: int = 40,
    min_chunk_size: int = 50
) -> list[str]:
    """
    Split text into overlapping chunks for embedding.

    Args:
        text: Full text to chunk.
        chunk_size: Target words per chunk.
        overlap: Words to overlap between consecutive chunks.
        min_chunk_size: Minimum words for a valid chunk.

    Returns:
        list[str]: List of text chunks.
    """
    words = text.split()
    if len(words) <= chunk_size:
        return [text]

    chunks = []
    start = 0

    while start < len(words):
        end = min(start + chunk_size, len(words))
        chunk = " ".join(words[start:end])

        if len(words[start:end]) >= min_chunk_size:
            chunks.append(chunk)

        if end >= len(words):
            break
        start += chunk_size - overlap

    return chunks


# Global embedder singleton
_embedder: Embedder | None = None


def get_embedder() -> Embedder:
    """Get the global embedder instance (loaded once)."""
    global _embedder
    if _embedder is None:
        _embedder = Embedder()
    return _embedder