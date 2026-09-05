"""Serializable metadata travels with every chunk and search result."""
from pydantic import BaseModel, Field


class Chunk(BaseModel):
    content: str
    document_id: str
    document_name: str
    page: int | None = None
    section: str = 'Unknown'
    chunk_id: str
    source: str


class DocumentMetadata(BaseModel):
    document_id: str
    document_name: str
    document_type: str
    pages: int
    uploaded_at: str
    sha256: str
    chunks_created: int = Field(ge=1)


class RetrievalResult(Chunk):
    score: float
