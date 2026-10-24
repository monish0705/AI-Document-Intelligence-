# Verification notes

Verified locally on Windows with Python 3.11 and Node.js.

- **7 automated API tests passed.** These cover lifecycle, saved reports, restart persistence, upload validation, stale/duplicate turns, role-filtered retrieval, source replacement, provider failure and retry, missing key behavior, and mocked OpenAI API contracts.
- **React build passed** with Vite. `npm install` reported zero known dependency vulnerabilities at installation.
- **Python dependency consistency check passed** (`pip check`).
- **Browser walkthrough completed in offline demo mode:** resume upload, role/length selection, three answers, final report, expanded source trace and restored report after refresh.
- **Textbook download/extraction/indexing verified:** the assignment-linked Bishop PDF contains readable text on 748 of 758 PDF pages; it produced 1,806 page-aware chunks using the offline embedding provider. The downloaded book and its vector index are excluded from Git.
- **Live OpenAI requests have not been verified:** no user API key was supplied. Tests exercise the HTTP contract with a mock transport; model quality and semantic retrieval must be checked with a real key before the company demo. Use both OpenAI providers and re-ingest the book, because embedding collections are separate.

One dependency emits a Starlette TestClient deprecation warning for httpx. It does not fail the tests. The local Windows sandbox initially blocked asyncio's internal loopback sockets; tests passed when run with local socket permissions.
