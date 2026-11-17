# AgentOps System Architecture & Engineering Blueprint

## Overview
AgentOps provides a unified, production-ready observability and evaluation platform for AI agents.

```mermaid
flowchart TD
    subgraph ClientLayer["Clients & Frontends"]
        Browser["Next.js Web App (Dashboard & Playground)"]
        CustomerAgent["Customer Python Agent / SDK"]
    end

    subgraph APILayer["FastAPI API Service (services/api)"]
        RateLimiter["Rate Limiter (Sliding Window / Redis)"]
        AuthMiddleware["Auth & Tenant Isolation Middleware"]
        PlaygroundRouter["Playground & Agent SSE Engine"]
        OTLPEndpoint["OTLP Ingestion Endpoint (/api/v1/telemetry)"]
        TraceRouter["Traces & Waterfalls API"]
        EvalRouter["Evaluation Engine API"]
        MetricsRouter["Metrics & Aggregations API"]
    end

    subgraph QueueCoordination["High-Speed Coordination (Redis / Stream Buffer)"]
        RedisStream["Redis Streams (stream:telemetry, stream:evals)"]
        RedisState["Rate Limit Tokens & Cooldowns"]
    end

    subgraph WorkerLayer["Background Workers (services/worker)"]
        TelemetryWorker["Telemetry Ingestion Worker"]
        EvalWorker["Evaluation Execution Worker"]
    end

    subgraph StorageLayer["Durable Relational Storage (PostgreSQL / SQLite)"]
        TenantsDB["Organizations, Projects, API Keys"]
        TracesDB["Traces, Spans, Tool Calls, Model Usages"]
        EvalsDB["Evaluation Datasets, Cases, Runs, Results"]
        AuditDB["Audit Logs, Alerts & Metrics Rollups"]
    end

    Browser -->|HTTP REST / SSE Stream| AuthMiddleware
    CustomerAgent -->|OTLP HTTP Traces / agentops-sdk| RateLimiter
    RateLimiter --> AuthMiddleware
    AuthMiddleware --> PlaygroundRouter
    AuthMiddleware --> OTLPEndpoint
    AuthMiddleware --> TraceRouter
    AuthMiddleware --> EvalRouter
    AuthMiddleware --> MetricsRouter

    PlaygroundRouter -->|Emit OTel Spans| RedisStream
    OTLPEndpoint -->|Buffer Spans| RedisStream
    RateLimiter <--> RedisState

    RedisStream --> TelemetryWorker
    RedisStream --> EvalWorker

    TelemetryWorker --> TracesDB
    EvalWorker --> EvalsDB
    TraceRouter --> TracesDB
    EvalRouter --> EvalsDB
    MetricsRouter --> TracesDB
    MetricsRouter --> EvalsDB
```

## Data Ingestion & Execution Flow
1. **Interactive Agent Execution (Playground)**:
   - User submits prompt via web client to `/api/v1/agent-runs`.
   - API initiates stateful execution loop with cancellation tokens.
   - Real-time Server-Sent Events (SSE) stream back: `agent_started`, `step_started`, `tool_executing`, `tool_result`, `agent_completed`.
   - Every execution emits a root Trace and child Spans (Agent Step -> Model Call -> Tool Execution).
2. **Telemetry Ingestion (SDK / OTLP)**:
   - Python SDK batches spans and sends to `/api/v1/telemetry/v1/traces`.
   - Ingestion validates project API key, applies sliding-window rate limit, and flushes to stream buffer.
   - Background worker processes batches and commits to relational database.
3. **Evaluation Engine**:
   - Automated evaluators score agent outputs across: Exact Match, JSON Validity, Tool Call Correctness, Schema Compliance, Latency Threshold, and LLM-as-Judge.
   - Versioned datasets ensure reproducible regression scores over time.
