"""Small HTTP API for the deployable DocuMind MVP."""
from functools import lru_cache
from fastapi import FastAPI, File, HTTPException, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

from app.config import Settings
from app.services.document_service import DocumentService
from app.services.embedding_service import create_embeddings
from app.services.retrieval_service import RetrievalService
from app.services.vector_store import VectorStore

app = FastAPI(title="DocuMind API", version="0.1.0")
app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_methods=["*"], allow_headers=["*"])

class Question(BaseModel):
    question: str

@lru_cache
def services():
    settings = Settings()
    embeddings = create_embeddings(settings)
    store = VectorStore(settings.vector_store_path, f"{settings.embedding_provider}:{settings.embedding_model}")
    return settings, embeddings, store

@app.get("/health")
def health():
    return {"status": "ok"}

@app.get("/documents")
def documents():
    return [d.model_dump() for d in services()[2].documents()]

@app.post("/documents/upload")
async def upload(file: UploadFile = File(...)):
    settings, embeddings, store = services()
    data = await file.read(settings.max_upload_mb * 1024 * 1024 + 1)
    try:
        doc, chunks = DocumentService(settings).parse(file.filename or "upload.txt", data)
        added = store.add(doc, chunks, embeddings.embed([c.content for c in chunks]))
        return {"document": doc.model_dump(), "chunks_created": len(chunks), "status": "indexed" if added else "already_indexed"}
    except Exception as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc

@app.post("/query")
def query(payload: Question):
    settings, embeddings, store = services()
    try:
        from app.services.local_model import create_local_model
        from app.services.rag_service import RAGService
        answer = RAGService(RetrievalService(embeddings, store, settings), create_local_model(settings)).ask(payload.question)
        return answer.model_dump()
    except Exception as exc:
        raise HTTPException(status_code=503, detail=f"Answer service unavailable: {exc}") from exc
