# ADR-0003: OpenTelemetry GenAI Semantic Conventions & Native Runtime Instrumentation

## Status
Accepted

## Context
Developers build AI agents using diverse frameworks (LangGraph, AutoGen, CrewAI, LlamaIndex, or vanilla OpenAI/Anthropic SDKs). If an observability platform enforces a proprietary schema, developers suffer vendor lock-in and high migration friction.

Furthermore, OpenTelemetry (OTel) has established the GenAI semantic conventions covering LLM calls, token usage, tool invocations, and agent workflows.

## Decision
1. **Adhere to OpenTelemetry GenAI Conventions**:
   - Spans represent Agent runs (`gen_ai.operation.name = "agent.run"`), model queries (`gen_ai.operation.name = "chat"`), and tool calls (`gen_ai.operation.name = "tool.execute"`).
   - Standard attributes: `gen_ai.system`, `gen_ai.request.model`, `gen_ai.usage.input_tokens`, `gen_ai.usage.output_tokens`, `gen_ai.usage.total_tokens`, `gen_ai.tool.name`.
2. **OTLP-Compatible HTTP Endpoint**:
   - `/api/v1/telemetry/v1/traces` accepts OpenTelemetry trace exports as well as simplified JSON payloads from the `agentops-sdk`.
3. **Standalone Native Runtime**:
   - Agent execution runtime includes deterministic, offline-capable agents (Research Assistant, Data Analysis Assistant) and mock modes so the entire platform functions out of the box without requiring external paid API keys.
   - When real API keys are configured (OpenAI, Anthropic, Gemini), the runtime routes dynamically while emitting identical OTel-compliant spans.

## Consequences
- Full interoperability with any standard OTel exporter or custom SDK.
- Predictable trace waterfalls matching industry-standard APM tools (e.g. Datadog, Honeycomb).
- Reproducible offline testing without billable API calls.
