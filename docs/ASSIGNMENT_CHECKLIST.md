# Assignment mapping

| Requirement | Implementation |
| --- | --- |
| React or Next.js | React with Vite, responsive interview workspace |
| Python backend | FastAPI routes and separate service modules |
| PDF/text resume | pypdf extraction, text validation and explicit scanned-PDF errors |
| Role selection | AI / ML Engineer and Backend Engineer |
| Skills, technology, domain | Rule-based skills, project lines, domain hints and experience extraction |
| Resume affects interview | Profile in query and LLM prompt; experience-based initial difficulty |
| Knowledge ingestion | PDF/TXT/MD upload or local CLI ingestion |
| Chunking | 220 words / 45 overlap, preserved PDF pages |
| Embeddings and vector database | OpenAI embeddings into persistent local Qdrant |
| Dynamic retrieval | Role + resume skills + projects + turn topic + prior answer |
| Contextual questions | OpenAI generation with retrieved text, profile and interview history |
| Traceability | Stored query, full retrieved passages, similarity, source/page, cited IDs and model |
| Session continuity | SQLite state, local session ID and recoverable browser answer draft |
| Questions and answers stored | Full session document persisted after each successful turn |
| Final summary | Topic coverage, transcript and explicitly heuristic observations |
| Environment configuration | Root .env, example config, no browser API key |
| Error handling | Invalid files, roles, blank answers, missing session, stale turns and provider failures |
| README | Setup, architecture, decisions, limits, commands and submission guide |
| Demo video | Recording guide included; candidate must record and submit video |
| GitHub repository | Source ready locally; candidate creates repository and pushes |

## Deliberate limits

- Offline mode is only a runnable demonstration: hashing is not semantic embedding and its question construction is deterministic. Full assignment evaluation should use both OpenAI providers and a supplied textbook.
- Real OpenAI calls require a candidate-provided key and available quota. Mock provider tests do not validate a live account.
- No OCR, authentication, role permissions, automated hiring scores, cloud infrastructure or multi-worker support.
- Source passages and model-provided IDs make question provenance inspectable. They do not guarantee every generated statement is supported.
- Chunk boundaries respect PDF pages, including front matter; no advanced layout reconstruction or equation parsing.
- Long textbook indexing is synchronous and intended for one local user. The UI waits for completion; there is no background job service.
- Source replacement removes chunks for the same role and filename before storing its new version. An unexpected storage failure during replacement would require re-ingestion.
- Only the newest 50 sessions are listed. Session IDs still open older records. Reports are stored; there is no edit/delete UI in this small assignment.
- Source listing is capped at 10,000 chunks, suitable for the provided book. This is not a bulk corpus indexing tool.
