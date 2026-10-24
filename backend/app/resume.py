import io
import re

from pypdf import PdfReader

SKILLS = {
    'Python': r'\bpython\b', 'JavaScript': r'\bjavascript\b|\btypescript\b',
    'SQL': r'\bsql\b|postgres|mysql|sqlite', 'FastAPI': r'fastapi|flask|django',
    'Machine learning': r'machine learning|scikit|sklearn', 'Deep learning': r'pytorch|tensorflow|deep learning',
    'NLP': r'\bnlp\b|natural language|transformer|\brag\b', 'Docker': r'\bdocker\b',
    'Redis': r'\bredis\b|caching', 'REST APIs': r'\brest\b|\bapis?\b',
    'Data analysis': r'pandas|numpy|data analysis', 'Git': r'\bgit\b|github',
}


def read_document(filename: str, content: bytes, max_bytes=25 * 1024 * 1024) -> list[tuple[int, str]]:
    if not content or len(content) > max_bytes:
        raise ValueError(f'Upload a non-empty file smaller than {max_bytes // (1024 * 1024)} MB.')
    if filename.lower().endswith('.pdf'):
        try:
            reader = PdfReader(io.BytesIO(content))
            if reader.is_encrypted:
                raise ValueError('Password-protected PDFs are not supported.')
            if len(reader.pages) > 1500:
                raise ValueError('PDF must contain fewer than 1500 pages.')
            pages = [(i + 1, p.extract_text() or '') for i, p in enumerate(reader.pages)]
        except ValueError:
            raise
        except Exception as exc:
            raise ValueError('Could not read this PDF. Upload a valid text-based PDF.') from exc
    elif filename.lower().endswith(('.txt', '.md')):
        try:
            pages = [(1, content.decode('utf-8-sig'))]
        except UnicodeDecodeError as exc:
            raise ValueError('Text files must use UTF-8 encoding.') from exc
    else:
        raise ValueError('Supported file types: PDF, TXT and Markdown.')
    if len(' '.join(t for _, t in pages).strip()) < 40:
        raise ValueError('Not enough readable text. Scanned PDFs require OCR first.')
    return pages


def parse_resume(filename: str, content: bytes) -> dict:
    text = '\n'.join(t for _, t in read_document(filename, content))[:30000]
    skills = [skill for skill, pattern in SKILLS.items() if re.search(pattern, text, re.I)]
    experience = [int(x) for x in re.findall(r'(\d+)\+?\s*years?', text, re.I)]
    years = max(experience, default=0)
    projects = [line.strip()[:240] for line in text.splitlines()
                if re.search(r'\b(built|developed|implemented|created|designed)\b|^\s*projects?\s*[:\-]', line, re.I)][:5]
    domains = [d for d in ['healthcare', 'finance', 'e-commerce', 'education', 'recommendation'] if d in text.lower()]
    return {'skills': skills, 'experience_years': years,
            'difficulty': 'advanced' if years >= 3 else 'intermediate' if years >= 1 else 'foundational',
            'projects': projects, 'domains': domains, 'text': text}
