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
        # A summary request is document-level, so semantic top-k filtering can
        # incorrectly produce empty evidence for short prompts like "summarize".
        if any(term in question.lower() for term in ('summary', 'summarize', 'summarise')):
            top_k = 100
            threshold = -1
        return self.store.search(
            self.embeddings.embed([question.strip()]),
            self.settings.top_k if top_k is None else top_k,
            self.settings.retrieval_score_threshold if threshold is None else threshold,
        )
