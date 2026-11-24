# AgentOps

**AI Agent Observability, Distributed Tracing & Evaluation Platform**

AgentOps is an AI infrastructure platform designed to help developers monitor, debug, evaluate and optimize AI agents across their entire execution lifecycle.

Traditional application monitoring shows whether an API succeeded or failed. AgentOps goes deeper, providing visibility into LLM requests, tool execution, retries, agent decisions, token consumption, latency and evaluation results.

**The goal is simple: make AI agents observable, measurable and reliable in production.**

**Project status:** Under active development. The architecture below describes the intended system; individual capabilities should be marked complete only after implementation and testing.

## 1. The Problem

An AI agent can produce the correct final answer while still behaving inefficiently.

For example, a research agent might return accurate company information but make five redundant tool calls, retry failed requests unnecessarily and consume significantly more tokens than expected.

The final output alone cannot reveal these problems.

AgentOps is designed to answer:

- What happened during an agent execution?
- Which LLM and tools were called?
- Where did the execution slow down?
- Why did a tool or model request fail?
- How many tokens were consumed, and what was the estimated cost?
- Did the agent complete the intended task correctly?
- Did a new agent version improve or degrade performance?

## 2. Core Capabilities

| Component | Purpose |
|---|---|
| Distributed Tracing | Track agent executions and nested operations |
| LLM Observability | Monitor provider requests, model latency and token usage |
| Tool Monitoring | Identify failed calls, retries and redundant operations |
| Agent Evaluations | Assess task success, correctness and tool usage |
| Performance Analytics | Analyze latency, errors, throughput and costs |
| Regression Testing | Compare agent behavior across versions |
| Developer Dashboard | Investigate traces, evaluation results and trends |
| Project Management | Organize agents, environments and API credentials |

## 3. System Architecture

The platform follows an asynchronous telemetry ingestion and processing architecture.

```text
AI Agent / LLM Application
          |
          | OpenTelemetry SDK / OTLP
          v
   Telemetry Collector
          |
          v
   FastAPI Ingestion API
          |
          | Authentication
          | Validation
          | Rate Limiting
          v
       Redis
  (Streams / Queue)
          |
          v
   Background Workers
          |
          | Trace Processing
          | Metrics Aggregation
          | Evaluation Jobs
          v
      PostgreSQL
          |
          v
    FastAPI Query API
          |
          v
    Next.js Dashboard
          |
          | Trace Explorer
          | Agent Evaluations
          | Performance Analytics
          | Error Investigation
```

Redis decouples telemetry ingestion from heavier processing tasks. PostgreSQL provides durable storage for traces, evaluations and project metadata.

For a production implementation, telemetry should be acknowledged only after it has reached an appropriately durable ingestion boundary.

## 4. End-to-End Execution Flow

**Step 1 — Instrumentation**

A developer instruments an AI agent using OpenTelemetry-compatible libraries.

The agent generates telemetry for model requests, tool executions, retrieval operations and errors.

**Step 2 — Telemetry ingestion**

The collector or SDK sends telemetry to the backend, where authentication, schema validation, tenant isolation and request limits are enforced.

**Step 3 — Asynchronous processing**

Validated events enter Redis Streams for background processing.

Workers normalize trace data, associate spans with their parent executions, calculate metrics and schedule evaluations.

**Step 4 — Persistent storage**

Processed traces, spans, metrics and evaluation results are stored in PostgreSQL.

**Step 5 — Analysis**

The evaluation engine assesses agent behavior using configurable checks, reference datasets and optional model-based evaluators.

**Step 6 — Visualization**

The dashboard presents execution timelines, errors, performance trends and evaluation outcomes.

## 5. Technology Stack

| Layer | Technology |
|---|---|
| Frontend | Next.js, React, TypeScript, Tailwind CSS |
| Backend | Python, FastAPI, Pydantic |
| Instrumentation | OpenTelemetry, OTLP |
| Background Processing | Redis Streams, Python workers |
| Database | PostgreSQL, SQLAlchemy Async |
| Database Migrations | Alembic |
| Authentication | Project-scoped API keys and application authentication |
| Infrastructure | Docker, Docker Compose |
| Testing | Pytest, Playwright, Locust or k6 |
| CI/CD | GitHub Actions |

### Why this architecture?

**FastAPI:** Asynchronous request handling and typed API contracts.

**OpenTelemetry:** Vendor-neutral instrumentation and trace context propagation.

**Redis Streams:** Buffers ingestion workloads and enables asynchronous processing, with consumer groups and recovery of pending messages.

**PostgreSQL:** Relational consistency for projects, traces, evaluations and access controls, with JSONB support for flexible telemetry attributes.

**Next.js:** Interactive dashboards, trace exploration and developer-facing product interfaces.

**Docker:** Reproducible local development and deployment environments.

## 6. Data Model

The initial relational schema is designed around:

| Entity | Responsibility |
|---|---|
| Organizations | Tenant boundaries |
| Projects | Agent applications and environments |
| API Keys | Scoped telemetry ingestion credentials |
| Traces | Complete agent executions |
| Spans | Individual operations within a trace |
| Evaluations | Scores, explanations and evaluation versions |
| Metrics | Aggregated operational measurements |

Each trace contains a trace ID, project ID, start time, duration, status and associated spans.

Each span contains its span ID, parent span ID, operation name, timestamps, status and selected attributes.

Database records are associated with their owning organization and project.

## 7. Agent Evaluation

AgentOps separates execution observability from behavioral evaluation.

**Observability asks:** What happened?

**Evaluation asks:** Was the behavior correct or acceptable?

Planned evaluation categories include:

- Task completion and correctness
- Tool selection and tool-call efficiency
- Repeated or unnecessary operations
- Response quality against reference answers
- Latency and token-budget compliance
- Regression detection across agent versions

Evaluation results must distinguish deterministic checks from model-graded judgments. Model-based scores are estimates, not guaranteed ground truth.

## 8. Example: Debugging an Agent

Consider an agent asked to retrieve information about a company.

**Final output:** The agent returns the correct answer.

**Execution trace:** The agent performed multiple repeated searches, encountered failed requests and required several retries.

**Evaluation:** A tool-efficiency check flags redundant calls even though the task-success evaluation passes.

**Developer action:** Investigate repeated retrieval, improve caching or adjust retry logic.

**Expected outcome:** Fewer unnecessary operations, lower latency and reduced inference costs.

This is an illustrative workflow, not a measured AgentOps benchmark.

## 9. Reliability and Scalability

The system is designed around the following engineering principles:

- Asynchronous telemetry ingestion
- Bounded queues and backpressure
- Atomic Redis rate limiting
- Consumer groups and retry policies
- Dead-letter handling for repeatedly failing events
- Idempotent writes and event deduplication
- PostgreSQL indexing and time-based partitioning when needed
- Trace sampling and configurable retention
- Health and readiness endpoints
- Graceful shutdown and worker recovery

### Delivery semantics

Redis Streams can support at-least-once processing when configured appropriately.

Workers should use stable event identifiers and idempotent database operations to prevent duplicate telemetry records.

## 10. Security and Privacy

Telemetry can contain sensitive prompts, customer information and tool arguments.

AgentOps should implement:

- Project-scoped API authentication
- Organization-level data isolation
- TLS for network communication
- Secret redaction and configurable content capture
- Least-privilege database access
- Rate limits and payload-size limits
- Audit logging for sensitive administrative actions
- Retention policies and deletion controls

Prompt and response content should not be captured by default without an explicit configuration decision.

## 11. Performance and Benchmarking

Performance claims must be based on reproducible tests.

Planned measurements include:

| Metric | Measurement |
|---|---|
| Ingestion throughput | Accepted telemetry events per second |
| API latency | p50, p95 and p99 |
| Queue lag | Time between ingestion and processing |
| Processing latency | Time to persist |
