# ADR-0001: Modular Monolith with Asynchronous Ingestion & Decoupled Workers

## Status
Accepted

## Context
AI Agent observability systems must ingest high-velocity OpenTelemetry spans, prompt/completion token metadata, and tool execution events with sub-millisecond overhead to avoid slowing down agent loops. At the same time, analytical workloads (trace waterfalls, metric rollups, evaluation runs, LLM-as-judge benchmarks) are read-heavy and computationally expensive.

A premature microservice architecture increases deployment complexity, network hops, and operational overhead, especially for local developer setups.

## Decision
We adopt a **Modular Monolith** structure:
- **`services/api`**: FastAPI service handling synchronous and streaming operations (Agent Playground SSE streams, OTLP ingestion, Trace and Evaluation queries, CRUD for Projects and Agents).
- **`services/worker`**: Dedicated background worker consuming ingestion and evaluation jobs from Redis Streams (or SQLite-backed queues in local offline setups).
- **Shared Data Layer**: SQLAlchemy 2.0 with async engine (`asyncpg` for PostgreSQL in production/Docker, `aiosqlite` for instant local offline testing).
- **Decoupled Python SDK**: `packages/python-sdk` instruments customer agents without hard-coupling to our backend runtime.

## Consequences
- Single repository and unified codebase for rapid end-to-end iteration.
- Easy deployment locally via a single command or Docker Compose.
- API service remains non-blocking and horizontally scalable.
- Clear migration path to dedicated microservices if ingestion traffic scales independently.
