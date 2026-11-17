# AGENTS.md — AgentOps Engineering Standards & Operational Rules

## 1. Project Mission & System Architecture
**AgentOps** is a production-grade AI Agent Observability, Tracing, Monitoring, and Evaluation SaaS platform. It enables developers to debug, trace, monitor, evaluate, and benchmark LLM agents with OpenTelemetry semantic conventions, distributed tracing waterfalls, real-time SSE streaming, and reproducible evaluation benchmarks.

### Architecture Topology
- **Apps**: `apps/web` (Next.js 14+ App Router, React 18/19, Tailwind CSS, Lucide Icons, Radix/shadcn-inspired design system).
- **Services**:
  - `services/api`: FastAPI (Python 3.11+ / 3.13), async SQLAlchemy 2.x, Pydantic v2, OTLP-compatible ingestion, SSE streaming agent runtime.
  - `services/worker`: Background stream processor consuming Redis/SQLite worker queues for evaluations and telemetry batch rollups.
- **Packages**:
  - `packages/python-sdk`: OpenTelemetry-compatible AgentOps Python instrumentation SDK (`agentops-sdk`).
  - `packages/shared`: Shared types, JSON schemas, and protocol definitions.
- **Persistence & Coordination**:
  - Relational Source of Truth: PostgreSQL / Async SQLite (fallback for standalone zero-dependency local dev).
  - High-Speed Coordination & Cache: Redis / Async In-Memory Redis Mock with atomic sliding window rate limiter and stream semantics.

---

## 2. Supported Technology Stack
- **Backend API**: Python, FastAPI, Uvicorn, SQLAlchemy 2.0 (async), Pydantic v2, Alembic.
- **Frontend**: Next.js (App Router), TypeScript, Tailwind CSS, Lucide React, Recharts.
- **Observability Standards**: OpenTelemetry GenAI semantic conventions (traces, spans, events, token attributes).
- **Agent Framework**: Multi-step stateful Agent Workflow Engine (inspired by LangGraph / ReAct agent loops) with native deterministic and mock execution modes.
- **Testing**: pytest, pytest-asyncio, httpx, vitest / jest / node test runner.

---

## 3. Design System & Approved Color Palette
AgentOps follows a restrained, high-density developer observability design:

### Light Mode
- Main Background: `#F8FAFC` (slate-50)
- Main Surface: `#FFFFFF`
- Primary Text: `#0F172A` (slate-900)
- Secondary Text: `#64748B` (slate-500)
- Primary Accent: `#2563EB` (blue-600)
- Subtle Accent: `#EFF6FF` (blue-50)
- Border: `#E2E8F0` (slate-200)

### Dark Mode
- Main Background: `#090E1A` (deep midnight)
- Main Surface: `#111827` (gray-900)
- Elevated Surface: `#1F2937` (gray-800)
- Primary Text: `#F8FAFC` (slate-50)
- Secondary Text: `#94A3B8` (slate-400)
- Primary Accent: `#60A5FA` (blue-400)

### Semantic Colors
- **Success / Passed**: `#10B981` (emerald-500)
- **Warning / Degraded**: `#F59E0B` (amber-500)
- **Error / Failed**: `#EF4444` (red-500)
- **Informational / Action**: `#2563EB` / `#60A5FA`

*Never make every panel colorful. Restraint, typographic hierarchy, and WCAG AA contrast are mandatory.*

---

## 4. Frontend Component & Accessibility Conventions
- Mobile and desktop responsive layouts with collapsible navigation.
- 8px spacing system (`p-2`, `p-4`, `p-6`, etc.).
- Skeleton states for all asynchronous data fetching.
- Visible, distinct indicators for Synthetic/Demo datasets vs live telemetry.
- Accessible keyboard navigation (`tabindex`, focus rings, ARIA roles for modals and accordions).
- No fake non-functional buttons. Every interactive element has an active handler or clear status.

---

## 5. Backend Layering & Dependency Rules
- **Domain Entities & Models**: Plain SQLAlchemy declarative models with UUID primary keys and UTC timestamps.
- **Schemas**: Strict Pydantic v2 schemas for request validation, response serialization, and OTLP mappings.
- **Repositories & Services**: Clean separation between database querying, business logic (evaluations, metrics aggregation), and HTTP route handlers.
- **Dependency Injection**: FastAPI `Depends` for database sessions, authentication, and service locators.

---

## 6. Database & Migration Standards
- UUID primary keys across all tables.
- All timestamps stored in UTC (`DateTime(timezone=True)`).
- Relational integrity: Strict Foreign Keys with cascade policies.
- Project & Tenant Scoping: Every query must filter by `project_id` or `organization_id`.
- Composite indexes on query paths: `(project_id, created_at DESC)`, `(trace_id, span_id)`.
- JSONB/JSON for extensible attributes (e.g. `raw_attributes`, `tool_parameters`).

---

## 7. Redis, Caching & Worker Standards
- Distributed sliding-window or token-bucket rate limiting returning HTTP 429 and `Retry-After`.
- Stream consumer groups for background trace ingestion and evaluation execution.
- Graceful degradation: If Redis is unavailable or unconfigured, system falls back to thread-safe in-memory sliding window and local queue without crashing.
- At-least-once delivery with idempotent database writes.

---

## 8. OpenTelemetry Instrumentation Rules
- Implement standard OpenTelemetry GenAI semantic conventions:
  - `gen_ai.system` (e.g. `openai`, `anthropic`, `agentops-runtime`)
  - `gen_ai.request.model`, `gen_ai.response.model`
  - `gen_ai.usage.input_tokens`, `gen_ai.usage.output_tokens`, `gen_ai.usage.total_tokens`
  - `gen_ai.operation.name` (`chat`, `execute_tool`, `agent_step`)
- Spans maintain strict parent-child relationships (`trace_id`, `span_id`, `parent_span_id`).
- Waterfalls accurately calculate duration `end_time - start_time`.

---

## 9. Security & Privacy Requirements
- API keys are hashed with SHA-256 before storage. Plain keys are shown only once upon generation.
- Default redaction of sensitive arguments/tokens. Raw payload storage is opt-in.
- Strict project-level authorization: Cross-tenant access attempts return 403 or 404.
- No client-side exposure of LLM provider keys.
- Comprehensive audit logging for administrative mutations.

---

## 10. API Conventions & Error Responses
- Versioned endpoints prefixed with `/api/v1/`.
- Uniform error structure: `{"error": {"code": "...", "message": "...", "details": ...}}`.
- Standard HTTP status codes: 200/201 for success, 400 validation, 401 unauthenticated, 403 forbidden, 404 not found, 429 rate limited, 500 internal server error.
- Health endpoints: `/health/live` and `/health/ready`.

---

## 11. Testing & Performance Requirements
- Target: 85%+ backend unit and integration test coverage.
- End-to-end tests for key workflows: Agent Chat SSE stream -> Trace Generation -> Waterfall Visualization -> Evaluation Run.
- Concurrency benchmarks for 1, 10, 25, 50, 100 concurrent requests.
- Distinct metrics tracking: Synthetic benchmarks vs Live LLM provider benchmarks.

---

## 12. Documentation Standards
- Architecture Decision Records (ADRs) in `docs/adr/`.
- Full OpenAPI / Swagger documentation at `/docs`.
- Dedicated guides for Architecture, API, Security, Evaluation Methodology, and Benchmarks.

---

## 13. Git & CI/CD Workflow
- Conventional Commits (`feat:`, `fix:`, `refactor:`, `test:`, `docs:`).
- Automated CI pipeline runs linting, type checks, and tests before release.

---

## 14. Definition of Done
A feature is complete ONLY when:
1. Code implements required functionality without mock stubs.
2. Unit and integration tests pass.
3. Relevant database tables/models and indexes are established.
4. UI component is integrated with live API endpoints and responsive.
5. Error states and loading states are handled cleanly.
6. Documentation is updated.

---

## 15. Prohibited Engineering Shortcuts
- ❌ NEVER deliver a frontend displaying hardcoded static numbers claiming to be live backend telemetry.
- ❌ NEVER simulate fake token-by-token reasoning that does not reflect actual agent steps.
- ❌ NEVER hardcode API keys or credentials.
- ❌ NEVER leave broken or inert buttons on any page.
- ❌ NEVER mix tenant data across projects.
- ❌ NEVER invent benchmark numbers without running an automated test script.
