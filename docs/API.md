# AgentOps REST API Documentation

Base URL: `http://localhost:8000/api/v1`

## Authentication
- **User JWT Bearer**: Standard header `Authorization: Bearer <jwt_token>`
- **Project API Key**: Header `X-AgentOps-Api-Key: aop_live_...`

---

## 1. Projects & Agents
- `GET /api/v1/projects` — List workspace projects.
- `POST /api/v1/projects` — Create a project.
  - Body: `{"name": "...", "description": "..."}`
- `GET /api/v1/projects/{project_id}/agents` — List agents in a project.
- `POST /api/v1/projects/{project_id}/agents` — Register an agent.
  - Body: `{"name": "...", "agent_type": "research|analysis|chat", "default_model": "..."}`
- `GET /api/v1/projects/{project_id}/api-keys` — List active API keys.
- `POST /api/v1/projects/{project_id}/api-keys` — Generate a new scoped API key.

---

## 2. Agent Execution & Playground
- `POST /api/v1/agent-runs?project_id={project_id}`
  - Initiates multi-step agent execution.
  - Body: `{"prompt": "...", "agent_id": "...", "stream": true}`
  - Returns: Server-Sent Events (`text/event-stream`):
    - `event: agent_started`
    - `event: step_started`
    - `event: tool_executing`
    - `event: tool_result`
    - `event: token`
    - `event: agent_completed`
- `POST /api/v1/agent-runs/{run_id}/cancel` — Cancel an in-flight execution.
- `GET /api/v1/agent-runs/{run_id}` — Retrieve run output, steps, token usage, and status.

---

## 3. Traces & OpenTelemetry Ingestion
- `GET /api/v1/projects/{project_id}/traces?page=1&page_size=25&status=ok` — Searchable trace list.
- `GET /api/v1/traces/{trace_id}` — Complete trace waterfall with hierarchical spans.
- `POST /api/v1/telemetry/v1/traces` — OTLP GenAI span ingestion endpoint.
  - Requires `X-AgentOps-Api-Key` header.
  - Body: `{"spans": [{"trace_id": "...", "span_id": "...", "name": "...", ...}]}`

---

## 4. Evaluations & Benchmarks
- `GET /api/v1/projects/{project_id}/evaluations/datasets` — List versioned evaluation datasets.
- `POST /api/v1/projects/{project_id}/evaluations/datasets` — Create dataset with test cases.
- `POST /api/v1/projects/{project_id}/evaluations/runs` — Trigger benchmark run against an agent.
- `GET /api/v1/projects/{project_id}/evaluations/runs` — History of evaluation runs and pass rates.

---

## 5. Metrics & Health
- `GET /api/v1/projects/{project_id}/metrics/overview` — Real stored metrics (success rate, p95 latency, tokens, cost).
- `GET /api/v1/projects/{project_id}/alerts` — Active alerts and warnings.
- `GET /health/live` — Liveness probe.
- `GET /health/ready` — Readiness probe.
