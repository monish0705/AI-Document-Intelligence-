import threading
from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI, File, Form, HTTPException, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field

from .config import Settings
from .generation import Generator
from .interview import InterviewService, candidate_view
from .knowledge import KnowledgeBase, ProviderError, ROLES
from .resume import parse_resume
from .storage import Store


class Answer(BaseModel):
    question_id: str
    answer: str = Field(min_length=1, max_length=10000)


def create_app(settings=None):
    settings = settings or Settings()
    lock = threading.RLock()  # One local worker; serialize state transitions and local Qdrant access.

    @asynccontextmanager
    async def lifespan(app):
        app.state.store = Store(settings.data_dir)
        app.state.kb = KnowledgeBase(settings)
        app.state.service = InterviewService(app.state.store, app.state.kb, Generator(settings))
        # No provider calls at startup. The UI can still explain missing-key errors.
        if settings.embedding_provider == 'hash':
            app.state.kb.seed()
        yield
        app.state.kb.client.close()

    app = FastAPI(title='Screenwise Interview API', version='1.0.0', lifespan=lifespan)
    app.add_middleware(CORSMiddleware, allow_origins=['http://localhost:5173', 'http://127.0.0.1:5173'],
                       allow_methods=['GET', 'POST'], allow_headers=['Content-Type'])

    @app.exception_handler(ProviderError)
    async def provider_error(request, exc):
        return JSONResponse(status_code=502, content={'detail': str(exc)})

    @app.exception_handler(ValueError)
    async def validation_error(request, exc):
        return JSONResponse(status_code=400, content={'detail': str(exc)})

    def role_check(role):
        if role not in ROLES:
            raise HTTPException(400, 'Select a supported role.')

    @app.get('/api/health')
    def health():
        return {'status': 'ok', 'llm_provider': settings.llm_provider,
                'embedding_provider': settings.embedding_provider,
                'model': {'openai': settings.model, 'ollama': settings.ollama_model,
                          'demo': 'deterministic-demo'}[settings.llm_provider],
                'demo': settings.llm_provider == 'demo' or settings.embedding_provider == 'hash',
                'roles': ROLES}

    @app.get('/api/knowledge')
    def knowledge():
        with lock:
            return {'sources': app.state.kb.sources(), 'embedding': app.state.kb.embedder.signature}

    @app.post('/api/knowledge', status_code=201)
    def ingest(role: str = Form(...), file: UploadFile = File(...)):
        role_check(role)
        content = file.file.read(25 * 1024 * 1024 + 1)
        with lock:
            count = app.state.kb.ingest(Path(file.filename or 'document').name, content, role)
        return {'chunks': count, 'source': file.filename, 'role': role}

    @app.get('/api/sessions')
    def sessions():
        return app.state.store.list()

    @app.post('/api/sessions', status_code=201)
    def start(name: str = Form(...), role: str = Form(...), total_questions: int = Form(5),
              resume: UploadFile = File(...)):
        role_check(role)
        name = name.strip()
        if not 1 <= len(name) <= 100 or not 3 <= total_questions <= 8:
            raise HTTPException(400, 'Enter a name (1-100 characters) and 3-8 questions.')
        parsed = parse_resume(resume.filename or '', resume.file.read(25 * 1024 * 1024 + 1))
        with lock:
            return candidate_view(app.state.service.new(name, role, parsed, total_questions))

    @app.get('/api/sessions/{session_id}')
    def session(session_id: str):
        result = app.state.store.get(session_id)
        if not result:
            raise HTTPException(404, 'Interview not found.')
        return candidate_view(result)

    @app.post('/api/sessions/{session_id}/answers')
    def answer(session_id: str, body: Answer):
        if not body.answer.strip():
            raise HTTPException(400, 'Write an answer before continuing.')
        with lock:
            try:
                return candidate_view(app.state.service.answer(session_id, body.question_id, body.answer.strip()))
            except LookupError as exc:
                raise HTTPException(404, str(exc)) from exc

    @app.get('/api/sessions/{session_id}/export')
    def export(session_id: str):
        result = session(session_id)
        return JSONResponse(result, headers={'Content-Disposition': f'attachment; filename="interview-{result["id"]}.json"'})

    return app


app = create_app()
