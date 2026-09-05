"""Validated settings; relative storage paths resolve against the repository."""
from pathlib import Path
from pydantic import Field, model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

ROOT = Path(__file__).resolve().parents[2]


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=ROOT / '.env', extra='ignore')
    embedding_provider: str = 'sentence_transformers'
    embedding_model: str = 'sentence-transformers/all-MiniLM-L6-v2'
    vector_store_path: Path = ROOT / 'backend/data/vector_store'
    chunk_size: int = Field(default=800, ge=2)
    chunk_overlap: int = Field(default=100, ge=0)
    top_k: int = Field(default=5, ge=1, le=100)
    retrieval_score_threshold: float = Field(default=0.65, ge=-1, le=1)
    max_upload_mb: int = Field(default=20, ge=1)

    @model_validator(mode='after')
    def validate_settings(self):
        if self.chunk_overlap >= self.chunk_size:
            raise ValueError('CHUNK_OVERLAP must be smaller than CHUNK_SIZE')
        if not self.vector_store_path.is_absolute():
            self.vector_store_path = ROOT / self.vector_store_path
        return self
