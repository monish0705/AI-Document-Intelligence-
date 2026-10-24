# Original demonstration notes: backend engineering

These original notes support the additional Backend Engineer role. The assignment's supplied books primarily cover ML; use the ML role and an uploaded textbook for the primary company demonstration.

## API design and validation
A REST API models resources and communicates results through HTTP status codes. Validate request shape at the boundary and business rules in a service layer. Return actionable errors without exposing credentials or internal tracebacks. Use pagination when collections grow and define a stable contract between frontend and backend. A creation request can return 201, while invalid input should return a client error. The database should remain consistent when a downstream service fails halfway through a workflow.

## SQL transactions and indexing
A transaction makes a set of related changes atomic. Database constraints protect invariants even when concurrent requests arrive. Indexes speed up selective reads but consume space and add write cost. An index should match actual query filters and ordering. Inspect query plans before optimizing. Parameterized queries separate data from SQL syntax. Use optimistic locking or a short transaction to prevent two concurrent requests from overwriting each other's state. Foreign keys enforce relationships between records.

## Caching and invalidation
A cache reduces repeated expensive work, but introduces stale data. Time-to-live bounds staleness while explicit invalidation ties freshness to writes. Cache keys must include every input that changes the result, including the role and model version in a retrieval system. Cache stampedes occur when many requests recompute the same expired key. Avoid caching private responses under shared keys. Measure hit rate and response latency to decide whether the complexity is justified.

## Concurrency and idempotency
Retries can repeat writes when a client does not know whether a request succeeded. Idempotency keys let the server recognize repeated operations. Check the current state before applying a state transition, and save the transition atomically. A stale question identifier must not overwrite a newer interview answer. Network calls inside long transactions can hold locks unnecessarily. For a local demonstration a single process and a lock can serialize changes; a distributed deployment needs database-backed concurrency control.

## Testing and reliability
Integration tests should exercise the API lifecycle using isolated persistent storage. Include invalid uploads, stale requests, missing sessions and downstream provider failures. Mock external APIs when testing error handling but clearly distinguish those tests from live provider validation. Use timeouts for external calls and preserve retryable user input. Health checks should separate application readiness from external provider availability. Logs should support debugging while avoiding resume content and API keys.
