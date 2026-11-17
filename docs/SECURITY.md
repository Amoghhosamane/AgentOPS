# AgentOps Security & Multi-Tenant Isolation Specifications

## 1. Authentication & API Key Hashing
- **Client / User Auth**: Industry-standard JWT Bearer tokens with configurable expiration and claims verification.
- **SDK & Ingestion Auth**: Project-scoped API keys with prefixing (e.g. `aop_live_...`).
  - Plaintext keys are never stored in the database.
  - Keys are hashed with SHA-256 upon generation. Plain values are displayed exactly once to the developer.

## 2. Strict Project-Level Multi-Tenant Isolation
- Ingestion queries require a valid `X-AgentOps-Api-Key` whose SHA-256 hash maps strictly to a specific `project_id`.
- Every database query for Traces, Spans, Agent Runs, and Evaluations enforces `WHERE project_id = :project_id`.
- Cross-tenant access attempts return HTTP 401 Unauthorized or HTTP 403 Forbidden.
- Automated regression tests in `tests/test_security_tenancy.py` verify that keys for Tenant A cannot read or write Tenant B's data.

## 3. Privacy & Payload Redaction
- By default, OpenTelemetry GenAI spans capture metadata, token counts, execution duration, and tool selection without logging sensitive user credentials or environment keys.
- Tool argument capture masks well-known credential parameters (`api_key`, `token`, `secret`, `password`).

## 4. Rate Limiting & Denial of Service Protection
- Atomic sliding-window rate limiting per API key and client IP.
- Default limit: 120 requests/minute for management APIs; 600 requests/minute for high-throughput `/telemetry` ingestion.
- Requests exceeding thresholds receive standard HTTP 429 with explicit `Retry-After` headers.
