import os
from dataclasses import dataclass
from pathlib import Path

from dotenv import load_dotenv

ROOT = Path(__file__).resolve().parents[2]
load_dotenv(ROOT / '.env')


@dataclass
class Settings:
    data_dir: Path = ROOT / os.getenv('DATA_DIR', 'backend/data')
    llm_provider: str = os.getenv('LLM_PROVIDER', 'demo')
    embedding_provider: str = os.getenv('EMBEDDING_PROVIDER', 'hash')
    api_key: str = os.getenv('OPENAI_API_KEY', '')
    model: str = os.getenv('OPENAI_MODEL', 'gpt-4o-mini')
    embedding_model: str = os.getenv('OPENAI_EMBEDDING_MODEL', 'text-embedding-3-small')
    ollama_url: str = os.getenv('OLLAMA_URL', 'http://localhost:11434')
    ollama_model: str = os.getenv('OLLAMA_MODEL', 'llama3.2')
    ollama_embedding_model: str = os.getenv('OLLAMA_EMBEDDING_MODEL', 'nomic-embed-text')

    def __post_init__(self):
        if self.llm_provider not in {'demo', 'openai', 'ollama'}:
            raise ValueError('LLM_PROVIDER must be demo, openai or ollama')
        if self.embedding_provider not in {'hash', 'openai', 'ollama'}:
            raise ValueError('EMBEDDING_PROVIDER must be hash, openai or ollama')
