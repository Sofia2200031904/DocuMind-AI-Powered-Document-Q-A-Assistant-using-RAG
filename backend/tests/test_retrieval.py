import numpy as np
import pytest
from app.config import Settings
from app.services.document_service import DocumentService
from app.services.retrieval_service import RetrievalService
from app.services.vector_store import VectorStore


class FakeEmbeddings:
    """Deterministic test double; real FAISS still executes in these tests."""
    identity = 'test:v1'

    def embed(self, texts):
        return np.array([[1, 0, 0] if 'leave' in t else [0, 1, 0] if 'API' in t
                         else [0, 0, 1] for t in texts], dtype=np.float32)


def build(tmp_path):
    settings = Settings(vector_store_path=tmp_path)
    store = VectorStore(tmp_path, FakeEmbeddings.identity)
    for name, content in [('handbook.txt', 'Annual leave is 20 days'), ('api.txt', 'API limit is 120')]:
        doc, chunks = DocumentService(settings).parse(name, content.encode())
        assert store.add(doc, chunks, FakeEmbeddings().embed([c.content for c in chunks]))
        assert not store.add(doc, chunks, FakeEmbeddings().embed([c.content for c in chunks]))
    return settings, store


def test_relevance_persistence_top_k_and_threshold(tmp_path):
    settings, _ = build(tmp_path)
    store = VectorStore(tmp_path, FakeEmbeddings.identity)
    retrieval = RetrievalService(FakeEmbeddings(), store, settings)
    results = retrieval.retrieve('leave policy')
    assert results[0].document_name == 'handbook.txt'
    assert results[0].score == pytest.approx(1)
    assert results[0].section == 'Unknown'
    assert len(retrieval.retrieve('leave', top_k=1, threshold=-1)) == 1
    assert len(retrieval.retrieve('leave', top_k=5, threshold=-1)) == 2
    assert retrieval.retrieve('astronomy') == []
    assert len(store.documents()) == 2


def test_empty_store_and_validation(tmp_path):
    store = VectorStore(tmp_path, 'test:v1')
    service = RetrievalService(FakeEmbeddings(), store, Settings())
    assert service.retrieve('leave') == []
    with pytest.raises(ValueError):
        service.retrieve(' ')
    with pytest.raises(ValueError):
        store.search(np.zeros((1, 3)), 2, 0.65)
    with pytest.raises(ValueError):
        service.retrieve('leave', top_k=0)


def test_model_mismatch_and_dimension(tmp_path):
    _, store = build(tmp_path)
    with pytest.raises(ValueError, match='Incompatible'):
        VectorStore(tmp_path, 'different-model').documents()
    with pytest.raises(ValueError, match='dimension'):
        store.search(np.ones((1, 4)), 2, 0.65)


def test_failed_snapshot_does_not_publish(tmp_path, monkeypatch):
    _, store = build(tmp_path)
    before = (tmp_path / 'CURRENT').read_text()
    doc, chunks = DocumentService(Settings()).parse('new.txt', b'new leave')
    def fail(*args):
        raise OSError('simulated interruption')
    monkeypatch.setattr('app.services.vector_store.os.replace', fail)
    with pytest.raises(OSError):
        store.add(doc, chunks, FakeEmbeddings().embed(['leave']))
    assert (tmp_path / 'CURRENT').read_text() == before
    assert len(store.documents()) == 2
