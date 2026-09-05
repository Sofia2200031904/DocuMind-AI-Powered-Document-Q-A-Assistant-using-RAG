"""Phase 2 composition helper; full OpenAI/Ollama abstraction follows in Phase 3."""
from langchain_ollama import ChatOllama
from app.config import Settings
from app.models.answers import AnswerDraft


def create_local_model(settings: Settings) -> ChatOllama:
    return ChatOllama(
        model=settings.ollama_model, base_url=settings.ollama_base_url,
        temperature=0, format=AnswerDraft.model_json_schema(),
        num_predict=1024, num_ctx=8192,
        client_kwargs={'timeout': settings.llm_timeout_seconds},
    )
