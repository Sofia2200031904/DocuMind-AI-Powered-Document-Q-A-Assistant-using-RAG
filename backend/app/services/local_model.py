"""Create the configured hosted/local chat model."""
from langchain_ollama import ChatOllama
from app.config import Settings
from app.models.answers import AnswerDraft


def create_local_model(settings):
    if settings.gemini_api_key:
        from langchain_google_genai import ChatGoogleGenerativeAI
        return ChatGoogleGenerativeAI(
            model=settings.gemini_model,
            google_api_key=settings.gemini_api_key,
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
