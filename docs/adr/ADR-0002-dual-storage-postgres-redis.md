# ADR-0002: Dual Storage Topology (Relational PostgreSQL + Redis Rate Limiter & Streams)

## Status
Accepted

## Context
Agent observability platforms require:
1. Low-latency, distributed rate limiting and temporary coordination per project/API-key/IP.
2. High-throughput ingestion queues to buffer bursts of telemetry spans before database persistence.
3. Structured, relational integrity with strict tenant isolation, foreign keys, and indexes for traces, spans, evaluations, and metrics.

Using a single NoSQL database (e.g. MongoDB) compromises transactional integrity and joins needed for complex multi-tenant analytics, while using only PostgreSQL for rate limiting creates heavy table write locks and connection exhaustion.

## Decision
We use a **Dual Storage Topology**:
1. **PostgreSQL (Asyncpg / SQLAlchemy 2.0)**:
   - Primary source of truth for: Organizations, Projects, API Keys, Agents, Agent Runs, Traces, Spans, Tool Calls, Evaluation Datasets, and Evaluation Results.
   - UUID primary keys, composite indexes on `(project_id, created_at DESC)` and `(trace_id, span_id)`.
   - JSONB used strictly for open-ended attributes and tool call arguments; structured columns for frequently queried metrics (latency, status, tokens, cost).
2. **Redis**:
   - Atomic sliding-window rate limiting using Redis server-side scripts (or atomic Redis hashes).
   - Redis Streams for decoupled worker queuing (`stream:telemetry`, `stream:evaluations`).
   - Short-lived caching for high-frequency dashboard aggregates.
   - Built-in graceful fallback to in-memory sliding window and memory queue when running in minimal standalone local setups.

## Consequences
- Guaranteed multi-tenant data isolation and ACID reliability.
- Sub-millisecond rate-limit checks without stressing database connections.
- Clean separation between ephemeral ingestion buffers and durable audit storage.
