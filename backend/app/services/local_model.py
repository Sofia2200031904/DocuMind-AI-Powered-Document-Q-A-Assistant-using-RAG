"""Create the configured hosted/local chat model."""
from langchain_ollama import ChatOllama
from app.config import Settings
from app.models.answers import AnswerDraft


def create_local_model(settings):
    if settings.openai_api_key:
        from langchain_openai import ChatOpenAI
        return ChatOpenAI(
            model=settings.openai_model,
            api_key=settings.openai_api_key,
            temperature=0,
            max_output_tokens=1024,
            timeout=settings.llm_timeout_seconds,
        )
    return ChatOllama(
        model=settings.ollama_model, base_url=settings.ollama_base_url,
        temperature=0, format=AnswerDraft.model_json_schema(),
        num_predict=1024, num_ctx=8192,
        client_kwargs={'timeout': settings.llm_timeout_seconds},
    )
