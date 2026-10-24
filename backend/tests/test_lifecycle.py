import io

import httpx
import pytest
from fastapi.testclient import TestClient
from pypdf import PdfWriter

from backend.app.config import ROOT, Settings
from backend.app.generation import Generator
from backend.app.knowledge import Embeddings, ProviderError, chunk_pages
from backend.app.main import create_app


@pytest.fixture
def settings(tmp_path):
    return Settings(data_dir=tmp_path, llm_provider='demo', embedding_provider='hash', api_key='')


@pytest.fixture
def client(settings):
    with TestClient(create_app(settings)) as c:
        yield c


def start(client, role='ml'):
    return client.post('/api/sessions', data={'name': 'Alex', 'role': role, 'total_questions': 3},
                       files={'resume': ('resume.txt', (ROOT / 'samples/resume_ml.txt').read_bytes(), 'text/plain')})


def test_full_interview_and_persistence(settings):
    with TestClient(create_app(settings)) as client:
        session = start(client).json()
        sid = session['id']
        assert session['resume']['skills'] and session['resume']['difficulty'] == 'intermediate'
        assert session['resume']['projects'][0].startswith('Built a healthcare')
        assert 'text' not in session['resume']
        for i in range(3):
            q = session['questions'][-1]
            assert 'expected_concepts' not in q
            assert q['sources'] and all(s['role'] == 'ml' for s in q['sources'])
            assert set(q['source_ids']).issubset({s['id'] for s in q['sources']})
            response = client.post(f'/api/sessions/{sid}/answers', json={
                'question_id': q['id'], 'answer': 'I would split data before preprocessing, compare to a baseline, and evaluate recall.'})
            assert response.status_code == 200, response.text
            session = response.json()
        assert session['status'] == 'completed'
        assert session['report']['answered'] == 3
        assert all(q['answer'] for q in session['questions'])
        assert client.get(f'/api/sessions/{sid}/export').json()['report'] == session['report']
        assert client.post(f'/api/sessions/{sid}/answers', json={'question_id': q['id'], 'answer': 'again'}).status_code == 400
    # New app and Qdrant client, same disk: sessions and vectors survive restart.
    with TestClient(create_app(settings)) as client:
        assert client.get(f'/api/sessions/{sid}').json()['status'] == 'completed'
        assert len(client.get('/api/sessions').json()) == 1
        assert client.get('/api/knowledge').json()['sources']


def test_validation_and_stale_submission(client):
    assert client.get('/api/sessions/missing').status_code == 404
    assert start(client, 'invalid').status_code == 400
    assert client.post('/api/sessions', data={'name': ' ', 'role': 'ml'},
                       files={'resume': ('resume.txt', b'a' * 100)}).status_code == 400
    assert client.post('/api/sessions', data={'name': 'Alex', 'role': 'ml'},
                       files={'resume': ('resume.exe', b'a' * 100)}).status_code == 400
    session = start(client).json()
    url = f'/api/sessions/{session["id"]}/answers'
    qid = session['questions'][-1]['id']
    assert client.post(url, json={'question_id': qid, 'answer': '  '}).status_code == 400
    assert client.post(url, json={'question_id': qid, 'answer': 'A valid answer'}).status_code == 200
    assert client.post(url, json={'question_id': qid, 'answer': 'Repeated answer'}).status_code == 400


def test_provider_failure_preserves_session_and_retry(client, monkeypatch):
    session = start(client).json()
    qid = session['questions'][0]['id']
    original = client.app.state.service.generator.question
    def fail(*args):
        raise ProviderError('Simulated provider outage')
    monkeypatch.setattr(client.app.state.service.generator, 'question', fail)
    response = client.post(f'/api/sessions/{session["id"]}/answers', json={'question_id': qid, 'answer': 'My draft'})
    assert response.status_code == 502
    stored = client.get(f'/api/sessions/{session["id"]}').json()
    assert stored['questions'][0]['answer'] is None
    monkeypatch.setattr(client.app.state.service.generator, 'question', original)
    assert client.post(f'/api/sessions/{session["id"]}/answers', json={'question_id': qid, 'answer': 'My draft'}).status_code == 200


def test_ingestion_deduplication_role_filtering(client):
    content = ('Transactions provide atomicity for order updates. SQL indexes speed reads but increase write costs. ' * 30).encode()
    for _ in range(2):
        response = client.post('/api/knowledge', data={'role': 'backend'}, files={'file': ('orders.txt', content)})
        assert response.status_code == 201
    sources = client.get('/api/knowledge').json()['sources']
    assert len([s for s in sources if s['source'] == 'orders.txt']) == 1
    results = client.app.state.kb.retrieve('backend', 'SQL transactions atomicity indexes')
    assert results[0]['source'] == 'orders.txt'
    assert all(s['role'] == 'backend' for s in results)
    assert not any(s['source'] == 'orders.txt' for s in client.app.state.kb.retrieve('ml', 'SQL transactions'))


def test_unreadable_pdf_and_chunk_overlap(client):
    stream = io.BytesIO()
    writer = PdfWriter(); writer.add_blank_page(200, 200); writer.write(stream)
    assert client.post('/api/knowledge', data={'role': 'ml'}, files={'file': ('scan.pdf', stream.getvalue())}).status_code == 400
    chunks = list(chunk_pages([(7, ' '.join(f'word{i}' for i in range(400)))]))
    assert chunks[0]['page'] == 7
    assert chunks[0]['text'].split()[-45:] == chunks[1]['text'].split()[:45]


def test_openai_contracts_with_mock_transport(settings, monkeypatch):
    settings.llm_provider = settings.embedding_provider = 'openai'
    settings.api_key = 'test-key-not-real'
    calls = []
    def respond(request):
        calls.append(request.url.path)
        if request.url.path.endswith('embeddings'):
            return httpx.Response(200, json={'data': [{'index': 0, 'embedding': [1.0, 0.0]}]})
        return httpx.Response(200, json={'choices': [{'message': {'content': '{"question":"How would you prevent leakage in your patient dataset?","topic":"Data leakage","rationale":"Your project uses healthcare data with repeated patients.","expected_concepts":["group splitting","leakage"],"source_ids":["source-1"]}'}}]})
    original_client = httpx.Client
    monkeypatch.setattr(httpx, 'Client', lambda **kwargs: original_client(transport=httpx.MockTransport(respond)))
    assert Embeddings(settings).encode(['data leakage']) == [[1.0, 0.0]]
    result = Generator(settings).question({'role': 'ml', 'resume': {'difficulty': 'intermediate'}, 'questions': []},
                                        'healthcare', [{'id': 'source-1', 'text': 'Group patients before splitting.'}])
    assert result['provider'] == 'openai'
    assert calls == ['/v1/embeddings', '/v1/chat/completions']


def test_openai_missing_key(settings):
    settings.llm_provider = 'openai'
    with TestClient(create_app(settings)) as client:
        response = start(client)
        assert response.status_code == 502
        assert 'OPENAI_API_KEY' in response.json()['detail']
        assert client.get('/api/sessions').json() == []
