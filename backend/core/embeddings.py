"""Canonical local-first embedding utility for SupremeAI.

Production Supabase ``ai_memory.embedding`` is ``vector(384)``.  This module
therefore guarantees that every pgvector embedding is exactly 384 dimensions.
"""

from __future__ import annotations

import math
import os

from core.logging_config import logger

LOW_MEMORY_MODE = os.getenv("LOW_MEMORY_MODE", "false").lower() == "true"
_HAS_SENTENCE_TRANSFORMERS = False

_LOCAL_MODEL_NAME = "all-MiniLM-L6-v2"
_LOCAL_DIM = 384
_PG_DIM = 384
_REMOTE_MODEL = "text-embedding-3-small"
_REMOTE_DIM = 384

_encoder = None
_embedding_cache: dict[str, list[float]] = {}
_cache_hits = 0
_cache_misses = 0


def get_cache_stats() -> dict[str, int]:
    """Return embedding cache hit/miss statistics."""
    return {"hits": _cache_hits, "misses": _cache_misses, "size": len(_embedding_cache)}


def get_local_encoder():
    """Lazy-load the local SentenceTransformer encoder (graceful on failure)."""
    global _encoder
    if _encoder is None and _HAS_SENTENCE_TRANSFORMERS:
        try:
            from sentence_transformers import SentenceTransformer

            logger.info(f"[embeddings] Loading local SentenceTransformer('{_LOCAL_MODEL_NAME}')...")
            _encoder = SentenceTransformer(_LOCAL_MODEL_NAME)
        except Exception as exc:
            logger.warning(f"[embeddings] Failed to load local encoder: {exc}")
    return _encoder


def hash_vectorize(text: str, size: int = _LOCAL_DIM) -> list[float]:
    """Pure-Python feature hashing fallback — zero-cost and exactly ``size`` dims."""
    vector = [0.0] * size
    words = [w.lower() for w in text.split() if len(w) > 1]
    if not words:
        vector[0] = 1.0
        return vector
    for word in words:
        h = abs(hash(word)) % size
        sign = 1 if (abs(hash(word)) // size) % 2 == 0 else -1
        vector[h] += sign
    norm = math.sqrt(sum(x * x for x in vector))
    if norm > 0:
        vector = [x / norm for x in vector]
    return vector


def local_embed(text: str) -> list[float] | None:
    """Return a 384-dim local embedding, or None if the encoder is unavailable."""
    enc = get_local_encoder()
    if enc is not None:
        try:
            vec = enc.encode(text).tolist()
            if len(vec) == _LOCAL_DIM:
                return vec
            logger.warning(
                f"[embeddings] local encoder returned {len(vec)} dims; expected {_LOCAL_DIM}"
            )
        except Exception as exc:
            logger.warning(f"[embeddings] local encode failed: {exc}")
    return None


def _pad_to_dim(vec: list[float], dim: int) -> list[float]:
    """Legacy compatibility helper; pgvector embeddings are never padded."""
    if len(vec) == dim:
        return vec
    if len(vec) > dim:
        return vec[:dim]
    return vec + [0.0] * (dim - len(vec))


def embed_for_pgvector(text: str, pg_dim: int = _PG_DIM) -> list[float]:
    """Return a pgvector-safe 384-dimensional embedding.

    The argument is retained for backward compatibility.  Production memory
    has a fixed ``vector(384)`` contract, so a caller asking for 1536 dims is
    normalized to 384 rather than creating an incompatible vector.
    """
    global _cache_hits, _cache_misses

    if pg_dim != _PG_DIM:
        logger.warning(
            f"[embeddings] requested pg_dim={pg_dim}, but ai_memory requires {_PG_DIM}; using {_PG_DIM}."
        )

    cache_key = f"{text}:{_PG_DIM}"
    if cache_key in _embedding_cache:
        _cache_hits += 1
        return _embedding_cache[cache_key].copy()

    _cache_misses += 1

    # Zero-cost local path first.
    local_vec = local_embed(text)
    if local_vec is not None:
        _embedding_cache[cache_key] = local_vec
        return local_vec.copy()

    # Optional remote fallback. text-embedding-3-small supports reduced dimensions.
    try:
        import litellm

        resp = litellm.embedding(model=_REMOTE_MODEL, input=text, dimensions=_REMOTE_DIM)
        vec = resp.data[0]["embedding"]
        if len(vec) == _PG_DIM:
            if len(_embedding_cache) >= 5000:
                _embedding_cache.clear()
            _embedding_cache[cache_key] = vec
            return vec.copy()
        logger.warning(f"[embeddings] remote provider returned {len(vec)} dims; expected {_PG_DIM}")
    except Exception as exc:
        logger.warning(f"[embeddings] LiteLLM embedding failed: {exc}; using local hash fallback")

    # Never return a dimension-incompatible vector to the memory layer.
    vec = hash_vectorize(text, size=_PG_DIM)
    if len(_embedding_cache) >= 5000:
        _embedding_cache.clear()
    _embedding_cache[cache_key] = vec
    return vec.copy()


def embed_query(text: str) -> list[float]:
    """Default 384-dimensional local-first embedding for semantic search."""
    return local_embed(text) or hash_vectorize(text, size=_PG_DIM)


class EmbeddingEngine:
    """Singleton embedding engine for local-first zero-cost semantic search."""

    _instance: EmbeddingEngine | None = None

    @classmethod
    def get_instance(cls) -> EmbeddingEngine:
        if cls._instance is None:
            cls._instance = cls()
        return cls._instance

    async def embed(self, text: str) -> list[float]:
        """Compute a 384-dimensional embedding asynchronously."""
        return embed_query(text)

    def cosine(self, v1: list[float], v2: list[float]) -> float:
        """Compute cosine similarity between equal-length vectors."""
        if not v1 or not v2 or len(v1) != len(v2):
            return 0.0
        dot = sum(a * b for a, b in zip(v1, v2, strict=True))
        norm1 = math.sqrt(sum(x * x for x in v1))
        norm2 = math.sqrt(sum(x * x for x in v2))
        if norm1 <= 0 or norm2 <= 0:
            return 0.0
        return dot / (norm1 * norm2)

    async def vector_search(self, query: str, corpus: list[dict], top_k: int = 5) -> list[dict]:
        """Search top-k matching documents using cosine similarity."""
        q_vec = await self.embed(query)
        scored = []
        for doc in corpus:
            doc_vec = doc.get("vector") or await self.embed(doc.get("text", ""))
            score = self.cosine(q_vec, doc_vec)
            scored.append((score, doc))
        scored.sort(key=lambda x: x[0], reverse=True)
        return [dict(doc, score=score) for score, doc in scored[:top_k]]
