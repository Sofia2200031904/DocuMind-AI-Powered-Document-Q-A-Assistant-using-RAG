"""Separate model-generated text from application-owned source provenance."""
from pydantic import BaseModel, ConfigDict, Field


class AnswerDraft(BaseModel):
    """The model may select evidence IDs, but cannot supply citation metadata."""
    model_config = ConfigDict(extra='forbid', strict=True)
    answer: str = Field(min_length=1, max_length=12000)
    evidence_ids: list[str] = Field(max_length=100)
    refused: bool


class SourceCitation(BaseModel):
    evidence_id: str
    document_id: str
    chunk_id: str
    document: str
    page: int | None
    section: str
    score: float


class GroundedAnswer(BaseModel):
    answer: str
    sources: list[SourceCitation]
    refused: bool
