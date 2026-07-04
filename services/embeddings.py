"""
Motor de embeddings — evolução do FAQEngine (rag_app.py) para o domínio de BOs.

Troca o backend Qdrant/all-MiniLM-L6-v2 por multilingual-e5-large (1024d),
com os prefixos `query:`/`passage:` exigidos pelo modelo e5 e cache de
embeddings no Redis (chave = SHA-256 do texto prefixado, TTL 24h).
"""

import hashlib
import os
from typing import List

import redis

os.environ.setdefault("HF_HUB_DOWNLOAD_TIMEOUT", "300")

from llama_index.embeddings.huggingface import HuggingFaceEmbedding

EMBED_MODEL_NAME = os.getenv("EMBED_MODEL_NAME", "intfloat/multilingual-e5-large")
REDIS_URL = os.getenv("REDIS_URL", "redis://localhost:6379/0")
CACHE_TTL_SECONDS = 24 * 60 * 60


class EmbeddingEngine:
    """Gera embeddings e5-large com prefixos query:/passage: e cache Redis."""

    def __init__(self, model_name: str = EMBED_MODEL_NAME, redis_url: str = REDIS_URL):
        self.model = HuggingFaceEmbedding(model_name=model_name, trust_remote_code=True)
        self.vector_dim = len(self.model.get_text_embedding("query: teste"))
        self.redis = redis.from_url(redis_url, decode_responses=False)

    @staticmethod
    def _cache_key(prefixed_text: str) -> str:
        digest = hashlib.sha256(prefixed_text.encode("utf-8")).hexdigest()
        return f"emb:{digest}"

    def _embed_with_cache(self, prefixed_text: str) -> List[float]:
        key = self._cache_key(prefixed_text)
        cached = self.redis.get(key)
        if cached is not None:
            import numpy as np
            return np.frombuffer(cached, dtype="float32").tolist()

        vector = self.model.get_text_embedding(prefixed_text)
        import numpy as np
        self.redis.set(key, np.asarray(vector, dtype="float32").tobytes(), ex=CACHE_TTL_SECONDS)
        return vector

    def embed_query(self, text: str) -> List[float]:
        return self._embed_with_cache(f"query: {text}")

    def embed_passage(self, text: str) -> List[float]:
        return self._embed_with_cache(f"passage: {text}")

    def embed_passages(self, texts: List[str]) -> List[List[float]]:
        return [self.embed_passage(t) for t in texts]
