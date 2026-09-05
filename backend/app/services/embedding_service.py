"""Provider interface prevents vector storage from depending on a model vendor."""
from typing import Protocol
import numpy as np
from app.config import Settings


class EmbeddingProvider(Protocol):
    identity: str

    def embed(self, texts: list[str]) -> np.ndarray: ...


class SentenceTransformerEmbeddings:
    def __init__(self, model_name: str):
        from sentence_transformers import SentenceTransformer
        self.identity = f'sentence_transformers:{model_name}'
        self.model = SentenceTransformer(model_name, device='cpu', trust_remote_code=False)

    def embed(self, texts: list[str]) -> np.ndarray:
        if not texts or any(not text.strip() for text in texts):
            raise ValueError('Embedding input must contain nonempty text')
        # Refuse silent model truncation, which would lose evidence in long chunks.
        lengths = [len(ids) for ids in self.model.tokenizer(texts)['input_ids']]
        if max(lengths) > self.model.max_seq_length:
            raise ValueError('Text exceeds embedding model token limit; reduce CHUNK_SIZE or query length')
        return np.asarray(self.model.encode(texts, normalize_embeddings=True,
                          convert_to_numpy=True, show_progress_bar=False), dtype=np.float32)


def create_embeddings(settings: Settings) -> EmbeddingProvider:
    if settings.embedding_provider != 'sentence_transformers':
        raise ValueError(f'Unsupported embedding provider: {settings.embedding_provider}')
    return SentenceTransformerEmbeddings(settings.embedding_model)
