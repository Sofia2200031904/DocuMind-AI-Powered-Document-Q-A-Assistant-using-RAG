"""Question embedding and confidence filtering, independent of routes and LLMs."""
from app.config import Settings
from app.models.documents import RetrievalResult
from app.services.embedding_service import EmbeddingProvider
from app.services.vector_store import VectorStore


class RetrievalService:
    def __init__(self, embeddings: EmbeddingProvider, store: VectorStore, settings: Settings):
        self.embeddings, self.store, self.settings = embeddings, store, settings

    def retrieve(self, question: str, top_k: int | None = None,
                 threshold: float | None = None) -> list[RetrievalResult]:
        if not question.strip():
            raise ValueError('Question cannot be empty')
        return self.store.search(
            self.embeddings.embed([question.strip()]),
            self.settings.top_k if top_k is None else top_k,
            self.settings.retrieval_score_threshold if threshold is None else threshold,
        )
