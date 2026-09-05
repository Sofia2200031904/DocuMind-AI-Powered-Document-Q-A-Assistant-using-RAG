"""Small CPU-only embeddings suitable for the free Render instance."""
import hashlib
from typing import Protocol
import numpy as np
from app.config import Settings


class EmbeddingProvider(Protocol):
    identity: str

    def embed(self, texts: list[str]) -> np.ndarray: ...


class SentenceTransformerEmbeddings:
    def __init__(self, model_name: str):
        # Keep the configured name in the identity so changing providers invalidates
        # stale indexes, but avoid loading PyTorch/Transformers (which exceeds 512 MB).
        self.identity = f'feature_hashing:{model_name}'
        self.dimension = 384

    def embed(self, texts: list[str]) -> np.ndarray:
        if not texts or any(not text.strip() for text in texts):
            raise ValueError('Embedding input must contain nonempty text')
        vectors = np.zeros((len(texts), self.dimension), dtype=np.float32)
        for row, text in enumerate(texts):
            tokens = text.lower().split()
            for token in tokens:
                digest = hashlib.blake2b(token.encode('utf-8'), digest_size=8).digest()
                index = int.from_bytes(digest[:4], 'little') % self.dimension
                sign = 1.0 if digest[4] & 1 else -1.0
                vectors[row, index] += sign
        norms = np.linalg.norm(vectors, axis=1, keepdims=True)
        return vectors / np.maximum(norms, 1e-12)


def create_embeddings(settings: Settings) -> EmbeddingProvider:
    if settings.embedding_provider != 'sentence_transformers':
        raise ValueError(f'Unsupported embedding provider: {settings.embedding_provider}')
    return SentenceTransformerEmbeddings(settings.embedding_model)
