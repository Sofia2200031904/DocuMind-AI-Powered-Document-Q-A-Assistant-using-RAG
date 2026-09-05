"""Offline LCEL behavior checks; these model doubles are not real-model evaluation."""
import json
import pytest
from langchain_core.messages import AIMessage
from langchain_core.runnables import RunnableLambda, RunnableSequence
from app.models.documents import RetrievalResult
from app.services.rag_service import RAGService, REFUSAL


def evidence(text='Employees receive 20 days of annual leave.', chunk_id='chunk1'):
    return RetrievalResult(content=text, document_id='doc1', document_name='handbook.pdf',
                           source='handbook.pdf', page=12, section='Unknown',
                           chunk_id=chunk_id, score=0.9)


class StubRetriever:
    def __init__(self, results):
        self.results = results
        self.questions = []

    def retrieve(self, question):
        self.questions.append(question)
        return self.results


@pytest.mark.parametrize('question,text,answer', [
    ('How much leave?', 'Employees receive 20 days of annual leave.', 'Employees receive 20 days.'),
    ('How many books?', 'Students may borrow eight books.', 'Students may borrow eight books.'),
    ('What is the API rate limit?', 'The limit is 120 requests per minute.', '120 requests per minute.'),
])
def test_actual_lcel_prompt_and_citations(question, text, answer):
    retriever = StubRetriever([evidence(text)])
    seen = []
    def model(prompt):
        seen.append(prompt.to_messages())
        return AIMessage(content=json.dumps(dict(answer=answer, evidence_ids=['S1'], refused=False)))
    service = RAGService(retriever, RunnableLambda(model))
    assert isinstance(service.chain, RunnableSequence)
    result = service.ask(question)
    assert retriever.questions == [question]
    assert question in seen[0][1].content and text in seen[0][1].content
    assert 'outside knowledge' in seen[0][0].content
    assert result.answer == answer and not result.refused
    assert result.sources[0].document == 'handbook.pdf'
    assert result.sources[0].page == 12
    assert result.sources[0].chunk_id == 'chunk1'


def test_empty_evidence_never_calls_model():
    def model(_):
        pytest.fail('Model must not run for empty evidence')
    result = RAGService(StubRetriever([]), RunnableLambda(model)).ask('Capital of France?')
    assert result.answer == REFUSAL and result.refused and result.sources == []


@pytest.mark.parametrize('output', [
    'not JSON',
    json.dumps(dict(answer='Invented', evidence_ids=['S999'], refused=False)),
    json.dumps(dict(answer='No evidence', evidence_ids=[], refused=False)),
    json.dumps(dict(answer=REFUSAL, evidence_ids=['S1'], refused=False)),
    json.dumps(dict(answer='Not supported', evidence_ids=['S1'], refused=True)),
    json.dumps(dict(answer='   ', evidence_ids=['S1'], refused=False)),
    json.dumps(dict(answer='Invented', evidence_ids=['S1'], refused=False, page=999)),
])
def test_invalid_or_refused_drafts_fail_closed(output):
    result = RAGService(StubRetriever([evidence()]), RunnableLambda(lambda _: output)).ask('Leave?')
    assert result.refused and result.sources == [] and result.answer == REFUSAL


def test_only_selected_sources_and_deduplication():
    model = RunnableLambda(lambda _: json.dumps(dict(answer='Supported', evidence_ids=['S2', 'S2'], refused=False)))
    result = RAGService(StubRetriever([evidence(), evidence('other evidence', 'chunk2')]), model).ask('Policy?')
    assert len(result.sources) == 1
    assert result.sources[0].chunk_id == 'chunk2'


def test_empty_question_and_provider_error():
    def unavailable(_):
        raise ConnectionError('Ollama offline')
    service = RAGService(StubRetriever([evidence()]), RunnableLambda(unavailable))
    with pytest.raises(ValueError):
        service.ask('   ')
    with pytest.raises(ConnectionError):
        service.ask('Leave?')
