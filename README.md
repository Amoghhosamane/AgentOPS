# AgentOps — AI Agent Observability, Tracing, Monitoring & Evaluation SaaS

[![CI Pipeline](https://github.com/agentops/agentops/actions/workflows/ci.yml/badge.svg)](https://github.com/agentops/agentops)
[![License: MIT](https://img.shields.io/badge/License-MIT-blue.svg)](LICENSE)
[![Python: 3.11+](https://img.shields.io/badge/Python-3.11+-blue.svg)](https://python.org)
[![Next.js: 14](https://img.shields.io/badge/Next.js-14-black.svg)](https://nextjs.org)

**AgentOps** is a production-grade observability, distributed tracing, and automated evaluation SaaS platform designed specifically for AI agents. It gives developers full visibility into multi-step agent workflows, tool invocations, token consumption, upstream latency percentiles, and regression test suites.

---

## 🌟 Key Features

1. **ChatGPT-Style Agent Playground**:
   - Real-time Server-Sent Events (SSE) streaming.
   - Observable execution step tracking (`agent_started` → `tool_executing` → `tool_result` → `token`).
   - One-click **View Trace** button connecting chat outputs directly to execution timelines.
   - Immediate cooperative cancellation support.

2. **Distributed Tracing & OpenTelemetry Engine**:
   - GenAI semantic convention compliance (`gen_ai.system`, `gen_ai.request.model`, `gen_ai.usage.*`, `gen_ai.tool.name`).
   - Waterfall visualization with parent-child span hierarchy and durations.
   - OTLP-compatible ingestion endpoint (`/api/v1/telemetry/v1/traces`).

3. **Evaluation Studio**:
   - Versioned golden benchmark datasets (`v1.0.0`).
   - Automated evaluators: Exact match, JSON schema compliance, keyword adherence, tool call accuracy, and latency thresholds.
   - Diagnostic per-case score breakdowns and failure analysis.

4. **Real-time Observability & KPI Dashboard**:
   - Total runs, success rate %, p95 latency, token consumption, model cost, and eval pass rates computed directly from stored telemetry.
   - Explicit labeling for synthetic demonstration records.

5. **Security & Multi-Tenant Isolation**:
   - Scoped API keys with SHA-256 one-way hashing.
   - Atomic sliding-window rate limiting with standard HTTP 429 and `Retry-After`.
   - Comprehensive cross-tenant isolation enforcement.

6. **Python Instrumentation SDK**:
   - Lightweight tracer context manager in `packages/python-sdk` for customer AI agents.

---

## 🏗️ Repository Architecture

```
agentops/
├── AGENTS.md                  # Operational engineering standards & rules
├── docker-compose.yml         # Containerized production stack (PostgreSQL, Redis, API, Web)
├── apps/
│   └── web/                   # Next.js 14 App Router, Tailwind CSS, Lucide Icons
├── services/
│   ├── api/                   # FastAPI backend, async SQLAlchemy 2.0, Pydantic v2
│   └── worker/                # Background stream processing workers
├── packages/
│   ├── python-sdk/            # OpenTelemetry-compatible AgentOps Python SDK
│   └── shared/                # Shared contracts and schemas
├── docs/                      # Technical documentation & ADRs
│   ├── ARCHITECTURE.md
│   ├── API.md
│   ├── DATABASE.md
│   ├── SECURITY.md
│   ├── EVALUATION_METHODOLOGY.md
│   ├── BENCHMARKS.md
│   ├── TEST_REPORT.md
│   ├── FINAL_ENGINEERING_REPORT.md
│   └── adr/                   # Architecture Decision Records (0001, 0002, 0003)
└── tests/                     # Pytest suite & concurrency benchmark harness
```

---

## 🚀 Quick Start (Local Development)

### 1. Start Backend API
```bash
# From workspace root
pip install -r services/api/requirements.txt
$env:PYTHONPATH="services/api:packages/python-sdk"
py -m uvicorn agentops_api.main:app --reload --port 8000
```
- API Documentation (Swagger): [http://localhost:8000/docs](http://localhost:8000/docs)
- Health Check: [http://localhost:8000/health/live](http://localhost:8000/health/live)

### 2. Start Frontend Web Dashboard
```bash
cd apps/web
npm install
npm run dev
```
- Dashboard & Playground UI: [http://localhost:3000](http://localhost:3000)

---

## 🧪 Testing & Verification

Run the automated test suite:
```bash
$env:PYTHONPATH="services/api"
py -m pytest tests/ -v
```

Run the empirical concurrency benchmark harness:
```bash
$env:PYTHONPATH="services/api"
py tests/benchmark_concurrency.py
```

Build the frontend web application:
```bash
cd apps/web
npm run build
```

---

## 📜 Documentation Index
- [Architecture & Data Flow](docs/ARCHITECTURE.md)
- [REST API Reference](docs/API.md)
- [Database & Relational Model](docs/DATABASE.md)
- [Security & Multi-Tenant Isolation](docs/SECURITY.md)
- [Evaluation Methodology](docs/EVALUATION_METHODOLOGY.md)
- [Empirical Concurrency Benchmarks](docs/BENCHMARKS.md)
- [Test Execution Report](docs/TEST_REPORT.md)
- [Final Engineering Report](docs/FINAL_ENGINEERING_REPORT.md)
- [ADR-0001: Modular Monolith Architecture](docs/adr/ADR-0001-modular-monolith-architecture.md)
- [ADR-0002: Dual Storage Topology](docs/adr/ADR-0002-dual-storage-postgres-redis.md)
- [ADR-0003: OpenTelemetry GenAI Standards](docs/adr/ADR-0003-opentelemetry-genai-standards.md)
