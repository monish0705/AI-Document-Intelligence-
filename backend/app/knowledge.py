"""Page-aware chunking, embeddings and a persistent local Qdrant vector database."""
import hashlib
import re
import uuid
from pathlib import Path

import httpx
import numpy as np
from qdrant_client import QdrantClient, models

from .config import ROOT
from .resume import read_document

ROLES = {'ml': 'AI / ML Engineer', 'backend': 'Backend Engineer'}
TOPICS = {
    'ml': ['generalization and overfitting', 'training validation data leakage',
           'classification precision recall', 'feature engineering regularization', 'model evaluation deployment'],
    'backend': ['API design validation', 'SQL transactions indexing', 'caching invalidation',
                'concurrency idempotency', 'testing reliability'],
}


class ProviderError(Exception):
    pass


class Embeddings:
    def __init__(self, settings):
        self.settings = settings
        self.provider = settings.embedding_provider
        self.model = {'hash': 'hash-word-bigram-v1', 'openai': settings.embedding_model,
                      'ollama': settings.ollama_embedding_model}[self.provider]

    @property
    def signature(self):
        return self.provider + ':' + self.model

    def encode(self, texts):
        if self.provider == 'hash':
            vectors = []
            for text in texts:
                words = re.findall(r'[a-z0-9]+', text.lower())
                features = words + [' '.join(pair) for pair in zip(words, words[1:])]
                vector = np.zeros(384, dtype=float)
                for word in features:
                    digest = hashlib.sha256(word.encode()).digest()
                    vector[int.from_bytes(digest[:4], 'little') % 384] += 1 if digest[4] % 2 else -1
                vector /= max(float(np.linalg.norm(vector)), 1)
                vectors.append(vector.tolist())
            return vectors
        try:
            with httpx.Client(timeout=120) as client:
                if self.provider == 'openai':
                    if not self.settings.api_key:
                        raise ProviderError('Add OPENAI_API_KEY to .env and restart the backend.')
                    response = client.post('https://api.openai.com/v1/embeddings',
                                           headers={'Authorization': f'Bearer {self.settings.api_key}'},
                                           json={'model': self.model, 'input': texts})
                    response.raise_for_status()
                    return [x['embedding'] for x in sorted(response.json()['data'], key=lambda x: x['index'])]
                response = client.post(self.settings.ollama_url + '/api/embed',
                                       json={'model': self.model, 'input': texts})
                response.raise_for_status()
                return response.json()['embeddings']
        except (httpx.HTTPError, KeyError, ValueError) as exc:
            raise ProviderError('Embedding provider failed. Check your key, model, network or Ollama server.') from exc


def chunk_pages(pages, size=220, overlap=45):
    for page, text in pages:
        words = text.split()
        for start in range(0, len(words), size - overlap):
            chunk = ' '.join(words[start:start + size])
            if len(chunk) >= 80:
                yield {'page': page, 'text': chunk, 'offset': start}
            if start + size >= len(words):
                break


class KnowledgeBase:
    def __init__(self, settings):
        self.embedder = Embeddings(settings)
        self.client = QdrantClient(path=str(settings.data_dir / 'vectors'))
        self.collection = 'knowledge_' + hashlib.sha256(self.embedder.signature.encode()).hexdigest()[:12]

    def count(self, role=None):
        if not self.client.collection_exists(self.collection):
            return 0
        return self.client.count(self.collection, count_filter=self.role_filter(role) if role else None).count

    @staticmethod
    def role_filter(role):
        return models.Filter(must=[models.FieldCondition(key='role', match=models.MatchValue(value=role))])

    def ingest(self, filename, content, role, source_kind='uploaded', max_bytes=25 * 1024 * 1024):
        chunks = list(chunk_pages(read_document(filename, content, max_bytes=max_bytes)))
        if not chunks:
            raise ValueError('Document has no usable text chunks.')
        checksum = hashlib.sha256(content).hexdigest()
        # Encode before replacing a previous version: provider failure leaves the old source intact.
        all_vectors = []
        for start in range(0, len(chunks), 32):
            all_vectors.extend(self.embedder.encode([c['text'] for c in chunks[start:start + 32]]))
        if not self.client.collection_exists(self.collection):
            self.client.create_collection(self.collection,
                vectors_config=models.VectorParams(size=len(all_vectors[0]), distance=models.Distance.COSINE))
        source = Path(filename).name
        self.client.delete(self.collection, models.FilterSelector(filter=models.Filter(must=[
            models.FieldCondition(key='role', match=models.MatchValue(value=role)),
            models.FieldCondition(key='source', match=models.MatchValue(value=source))])))
        points = [models.PointStruct(id=str(uuid.uuid5(uuid.NAMESPACE_URL,
                    f'{role}:{source}:{checksum}:{c["page"]}:{c["offset"]}')), vector=vector,
                    payload={**c, 'role': role, 'source': source, 'source_kind': source_kind,
                             'checksum': checksum}) for c, vector in zip(chunks, all_vectors)]
        for start in range(0, len(points), 64):
            self.client.upsert(self.collection, points=points[start:start + 64])
        return len(chunks)

    def seed(self):
        for role in ROLES:
            if not self.count(role):
                for path in sorted((ROOT / 'knowledge' / role).glob('*.md')):
                    self.ingest(path.name, path.read_bytes(), role, 'sample notes')

    def sources(self):
        if not self.count():
            return []
        records, _ = self.client.scroll(self.collection, limit=10000, with_vectors=False)
        grouped = {}
        for record in records:
            p = record.payload
            key = (p['role'], p['source'])
            grouped.setdefault(key, {'role': p['role'], 'source': p['source'],
                                    'kind': p['source_kind'], 'chunks': 0})['chunks'] += 1
        return list(grouped.values())

    def retrieve(self, role, query, limit=4):
        if not self.count(role):
            raise ValueError('Upload knowledge documents for this role first.')
        results = self.client.query_points(self.collection, query=self.embedder.encode([query])[0],
            query_filter=self.role_filter(role), limit=limit, with_payload=True).points
        return [{'id': str(r.id), 'score': round(r.score, 4), **r.payload} for r in results]
