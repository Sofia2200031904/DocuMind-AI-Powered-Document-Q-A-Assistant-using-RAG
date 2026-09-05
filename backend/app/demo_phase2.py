"""Run real local-model demonstrations; no canned answers or substituted models."""
import json
from app.config import Settings
from app.services.embedding_service import create_embeddings
from app.services.local_model import create_local_model
from app.services.rag_service import RAGService
from app.services.retrieval_service import RetrievalService
from app.services.vector_store import VectorStore

QUESTIONS = [
    'How many days of paid annual leave do employees receive?',
    'What is the Harbor API rate limit per access token?',
    'How many books may students borrow and for how long?',
    'What is the capital of France?',
]


def main():
    settings = Settings()
    embeddings = create_embeddings(settings)
    retriever = RetrievalService(embeddings, VectorStore(settings.vector_store_path, embeddings.identity), settings)
    rag = RAGService(retriever, create_local_model(settings))
    for question in QUESTIONS:
        result = rag.ask(question)
        print(json.dumps({'question': question, **result.model_dump()}, ensure_ascii=False), flush=True)


if __name__ == '__main__':
    main()
