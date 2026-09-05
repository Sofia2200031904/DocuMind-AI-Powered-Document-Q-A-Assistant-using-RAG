"""Persistent exact cosine search with JSON metadata and atomic snapshots.

The process lock serializes writers and readers across CLI invocations. Each
commit writes a new immutable snapshot before atomically publishing CURRENT.
Only load stores produced locally: FAISS files are not an untrusted upload format.
"""
import json
import os
from pathlib import Path
from uuid import uuid4

import faiss
import numpy as np
from filelock import FileLock

from app.models.documents import Chunk, DocumentMetadata, RetrievalResult


class VectorStore:
    def __init__(self, path: Path, embedding_identity: str):
        self.path = path
        self.identity = embedding_identity
        path.mkdir(parents=True, exist_ok=True)
        self.lock = FileLock(str(path / '.lock'))

    def _load(self):
        current = self.path / 'CURRENT'
        if not current.exists():
            return None, [], []
        name = current.read_text(encoding='utf-8').strip()
        if len(name) != 32 or any(c not in '0123456789abcdef' for c in name):
            raise ValueError('Invalid vector store snapshot')
        state = json.loads((self.path / f'{name}.json').read_text(encoding='utf-8'))
        if state['version'] != 1 or state['embedding_identity'] != self.identity:
            raise ValueError('Incompatible index/model: use a new VECTOR_STORE_PATH and reindex')
        index = faiss.read_index(str(self.path / f'{name}.faiss'))
        chunks = [Chunk.model_validate(c) for c in state['chunks']]
        documents = [DocumentMetadata.model_validate(d) for d in state['documents']]
        if index.ntotal != len(chunks):
            raise ValueError('Vector count does not match metadata')
        return index, chunks, documents

    @staticmethod
    def _normalize(vectors: np.ndarray) -> np.ndarray:
        vectors = np.array(vectors, dtype=np.float32, order='C', copy=True)
        if vectors.ndim != 2 or not vectors.shape[0] or not vectors.shape[1]:
            raise ValueError('Expected a nonempty embedding matrix')
        if not np.isfinite(vectors).all() or np.any(np.linalg.norm(vectors, axis=1) == 0):
            raise ValueError('Embeddings must be finite and nonzero')
        faiss.normalize_L2(vectors)
        return vectors

    def add(self, document: DocumentMetadata, chunks: list[Chunk], vectors: np.ndarray) -> bool:
        vectors = self._normalize(vectors)
        if len(chunks) != len(vectors) or len(chunks) != document.chunks_created:
            raise ValueError('Chunk and vector counts differ')
        if any(c.document_id != document.document_id for c in chunks):
            raise ValueError('Chunk belongs to a different document')
        with self.lock:
            index, stored, documents = self._load()
            if any(d.sha256 == document.sha256 and d.document_name == document.document_name
                   for d in documents):
                return False
            if index is None:
                index = faiss.IndexFlatIP(vectors.shape[1])
            if index.d != vectors.shape[1]:
                raise ValueError('Embedding dimensions differ; reindex with the current model')
            index.add(vectors)
            name = uuid4().hex
            faiss.write_index(index, str(self.path / f'{name}.faiss'))
            state = dict(version=1, embedding_identity=self.identity,
                         chunks=[c.model_dump() for c in stored + chunks],
                         documents=[d.model_dump() for d in documents + [document]])
            with (self.path / f'{name}.json').open('w', encoding='utf-8') as file:
                json.dump(state, file, ensure_ascii=False)
                file.flush()
                os.fsync(file.fileno())
            pointer = self.path / f'{name}.tmp'
            pointer.write_text(name, encoding='utf-8')
            os.replace(pointer, self.path / 'CURRENT')
            return True

    def search(self, vector: np.ndarray, top_k: int, threshold: float) -> list[RetrievalResult]:
        if not 1 <= top_k <= 100 or not -1 <= threshold <= 1:
            raise ValueError('Invalid retrieval top_k or threshold')
        vector = self._normalize(vector)
        if vector.shape[0] != 1:
            raise ValueError('Search accepts one query vector')
        with self.lock:
            index, chunks, _ = self._load()
            if index is None or not index.ntotal:
                return []
            if vector.shape[1] != index.d:
                raise ValueError('Query embedding dimension does not match index')
            scores, positions = index.search(vector, min(top_k, index.ntotal))
            return [RetrievalResult(**chunks[int(i)].model_dump(), score=float(np.clip(s, -1, 1)))
                    for s, i in zip(scores[0], positions[0]) if i >= 0 and s >= threshold]

    def documents(self) -> list[DocumentMetadata]:
        with self.lock:
            return self._load()[2]
