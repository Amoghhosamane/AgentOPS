"""AgentOps Execution Runtime & Stateful Multi-Step Agent Engine.

Supports:
1. Research Assistant (planning -> search -> summarize -> final answer).
2. Data Analysis Assistant (read dataset -> statistical computation -> structured output).
3. Real-time Server-Sent Events (SSE) streaming with cancellation.
4. Automatic OpenTelemetry GenAI semantic span generation.
"""

import asyncio
import json
import time
import uuid
from datetime import datetime, timezone
from typing import AsyncGenerator, Dict, Any, List, Optional
from agentops_api.models import AgentRun, Trace, Span
from agentops_api.database import get_db_context


class AgentCancellationException(Exception):
    """Raised when an agent run is cancelled by client or timeout."""
    pass


# Global registry of running tasks for cancellation
RUNNING_TASKS: Dict[str, asyncio.Event] = {}


# Deterministic offline tools
def search_knowledge_base(query: str) -> str:
    """Mock safe knowledge base retrieval tool."""
    query_lower = query.lower()
    if "agentops" in query_lower or "observability" in query_lower:
        return "AgentOps is an AI agent observability, tracing, and evaluation platform utilizing OpenTelemetry semantic conventions and real-time SSE streaming."
    elif "opentelemetry" in query_lower or "otel" in query_lower:
        return "OpenTelemetry provides vendor-neutral APIs, SDKs, and tools to instrument, generate, and export telemetry data such as traces, metrics, and logs."
    elif "evaluation" in query_lower or "benchmarking" in query_lower:
        return "Agent evaluation measures task accuracy, tool call correctness, latency percentiles, and schema compliance against versioned golden datasets."
    else:
        return f"Retrieved 3 indexed articles relating to '{query}' covering architecture, latency optimization, and reliability standards."


def calculate_statistics(data: List[float]) -> Dict[str, float]:
    """Safe mathematical computation tool."""
    if not data:
        return {"count": 0, "mean": 0.0, "min": 0.0, "max": 0.0}
    return {
        "count": len(data),
        "mean": round(sum(data) / len(data), 2),
        "min": min(data),
        "max": max(data),
        "sum": round(sum(data), 2)
    }


async def run_agent_workflow(
    project_id: str,
    prompt: str,
    agent_id: Optional[str] = None,
    agent_type: str = "research",
    model: str = "mock-agent-v1",
    is_synthetic: bool = False
) -> AsyncGenerator[str, None]:
    """
    Executes a multi-step agent loop, yielding formatted Server-Sent Events (SSE).
    Persists AgentRun, Trace, and Spans to the database upon completion.
    """
    run_id = str(uuid.uuid4())
    trace_id = uuid.uuid4().hex
    root_span_id = uuid.uuid4().hex[:16]
    cancel_event = asyncio.Event()
    RUNNING_TASKS[run_id] = cancel_event

    start_time = datetime.now(timezone.utc)
    start_ts = time.time()
    
    # Trace accumulator
    collected_spans: List[Dict[str, Any]] = []
    total_prompt_tokens = len(prompt.split()) * 4 + 50
    total_completion_tokens = 0
    final_output = ""
    error_message: Optional[str] = None
    step_count = 0

    try:
        # 1. Event: Agent Started
        yield f"event: agent_started\ndata: {json.dumps({'run_id': run_id, 'trace_id': trace_id, 'prompt': prompt, 'agent_type': agent_type, 'model': model})}\n\n"
        await asyncio.sleep(0.05)

        # Step 1: Planning / Deconstruction
        if cancel_event.is_set():
            raise AgentCancellationException("Run cancelled by user")
        step_count += 1
        step1_span_id = uuid.uuid4().hex[:16]
        step1_start = datetime.now(timezone.utc)
        step1_ts = time.time()

        yield f"event: step_started\ndata: {json.dumps({'step': 1, 'name': 'task_planning', 'description': 'Analyzing user prompt and planning tool execution sequence'})}\n\n"
        await asyncio.sleep(0.15)

        step1_duration = round((time.time() - step1_ts) * 1000, 2)
        step1_tokens = 45
        total_completion_tokens += step1_tokens

        collected_spans.append({
            "span_id": step1_span_id,
            "parent_span_id": root_span_id,
            "name": "agent.plan",
            "operation_name": "agent.plan",
            "kind": "INTERNAL",
            "start_time": step1_start,
            "end_time": datetime.now(timezone.utc),
            "duration_ms": step1_duration,
            "prompt_tokens": total_prompt_tokens,
            "completion_tokens": step1_tokens,
            "total_tokens": total_prompt_tokens + step1_tokens,
            "attributes": {"step_number": 1, "plan": "Retrieve domain context and compute analysis."}
        })

        # Step 2: Tool Invocation
        if cancel_event.is_set():
            raise AgentCancellationException("Run cancelled by user")
        step_count += 1
        step2_span_id = uuid.uuid4().hex[:16]
        step2_start = datetime.now(timezone.utc)
        step2_ts = time.time()

        if "analy" in prompt.lower() or "calc" in prompt.lower() or "data" in prompt.lower():
            tool_name = "calculate_statistics"
            tool_args = {"data": [12.5, 45.0, 78.2, 92.4, 33.1, 88.0]}
            yield f"event: tool_executing\ndata: {json.dumps({'step': 2, 'tool_name': tool_name, 'args': tool_args})}\n\n"
            await asyncio.sleep(0.18)
            tool_res = calculate_statistics(tool_args["data"])
        else:
            tool_name = "search_knowledge_base"
            tool_args = {"query": prompt}
            yield f"event: tool_executing\ndata: {json.dumps({'step': 2, 'tool_name': tool_name, 'args': tool_args})}\n\n"
            await asyncio.sleep(0.18)
            tool_res = search_knowledge_base(prompt)

        yield f"event: tool_result\ndata: {json.dumps({'step': 2, 'tool_name': tool_name, 'result': tool_res})}\n\n"
        step2_duration = round((time.time() - step2_ts) * 1000, 2)

        collected_spans.append({
            "span_id": step2_span_id,
            "parent_span_id": root_span_id,
            "name": f"tool.{tool_name}",
            "operation_name": "tool.execute",
            "kind": "CLIENT",
            "start_time": step2_start,
            "end_time": datetime.now(timezone.utc),
            "duration_ms": step2_duration,
            "tool_name": tool_name,
            "tool_args": tool_args,
            "tool_result": tool_res,
            "prompt_tokens": 0,
            "completion_tokens": 0,
            "total_tokens": 0,
            "attributes": {"gen_ai.tool.name": tool_name}
        })

        # Step 3: Synthesis & Final Answer Generation
        if cancel_event.is_set():
            raise AgentCancellationException("Run cancelled by user")
        step_count += 1
        step3_span_id = uuid.uuid4().hex[:16]
        step3_start = datetime.now(timezone.utc)
        step3_ts = time.time()

        yield f"event: step_started\ndata: {json.dumps({'step': 3, 'name': 'response_synthesis', 'description': 'Generating grounded final synthesis'})}\n\n"
        await asyncio.sleep(0.1)

        if tool_name == "calculate_statistics":
            final_output = (
                f"### Statistical Analysis Results\n\n"
                f"Computed metrics for sample dataset:\n"
                f"- **Data Points Count**: {tool_res['count']}\n"
                f"- **Mean Value**: {tool_res['mean']}\n"
                f"- **Range**: Min {tool_res['min']} to Max {tool_res['max']}\n"
                f"- **Total Aggregate Sum**: {tool_res['sum']}\n\n"
                f"The distribution demonstrates consistent performance across observation windows."
            )
        else:
            final_output = (
                f"### Agent Research Summary\n\n"
                f"Based on our knowledge base scan regarding **'{prompt}'**:\n\n"
                f"> {tool_res}\n\n"
                f"Key Takeaway: The system verifies proper OpenTelemetry semantic standards, "
                f"sliding-window distributed rate limiting, and reproducible automated evaluation datasets."
            )

        # Stream final tokens in chunks
        words = final_output.split(" ")
        for i in range(0, len(words), 4):
            if cancel_event.is_set():
                raise AgentCancellationException("Run cancelled by user")
            chunk = " ".join(words[i:i+4]) + " "
            yield f"event: token\ndata: {json.dumps({'chunk': chunk})}\n\n"
            await asyncio.sleep(0.04)

        step3_duration = round((time.time() - step3_ts) * 1000, 2)
        step3_tokens = len(words) * 2
        total_completion_tokens += step3_tokens

        collected_spans.append({
            "span_id": step3_span_id,
            "parent_span_id": root_span_id,
            "name": "chat.completion",
            "operation_name": "chat",
            "kind": "CLIENT",
            "start_time": step3_start,
            "end_time": datetime.now(timezone.utc),
            "duration_ms": step3_duration,
            "gen_ai_system": "agentops-runtime",
            "gen_ai_model": model,
            "prompt_tokens": total_prompt_tokens,
            "completion_tokens": step3_tokens,
            "total_tokens": total_prompt_tokens + step3_tokens,
            "attributes": {"gen_ai.request.model": model, "gen_ai.response.model": model}
        })

        run_status = "completed"

    except AgentCancellationException as ce:
        run_status = "cancelled"
        error_message = str(ce)
        yield f"event: agent_cancelled\ndata: {json.dumps({'run_id': run_id, 'reason': error_message})}\n\n"
    except Exception as exc:
        run_status = "failed"
        error_message = str(exc)
        yield f"event: agent_failed\ndata: {json.dumps({'run_id': run_id, 'error': error_message})}\n\n"
    finally:
        RUNNING_TASKS.pop(run_id, None)

    end_time = datetime.now(timezone.utc)
    total_duration_ms = round((time.time() - start_ts) * 1000, 2)
    total_tokens = total_prompt_tokens + total_completion_tokens
    # Standard mock pricing: $0.0015 / 1k tokens
    estimated_cost = round((total_tokens / 1000.0) * 0.0015, 6)

    # Root span covering the entire agent execution
    root_span = {
        "span_id": root_span_id,
        "parent_span_id": None,
        "name": f"agent.run [{agent_type}]",
        "operation_name": "agent.run",
        "kind": "SERVER",
        "status": "ok" if run_status == "completed" else "error",
        "status_message": error_message,
        "start_time": start_time,
        "end_time": end_time,
        "duration_ms": total_duration_ms,
        "gen_ai_system": "agentops-runtime",
        "gen_ai_model": model,
        "prompt_tokens": total_prompt_tokens,
        "completion_tokens": total_completion_tokens,
        "total_tokens": total_tokens,
        "attributes": {
            "agent_type": agent_type,
            "total_steps": step_count,
            "is_synthetic": is_synthetic
        }
    }
    collected_spans.insert(0, root_span)

    # Persist records to database
    try:
        async with get_db_context() as session:
            agent_run = AgentRun(
                id=run_id,
                project_id=project_id,
                agent_id=agent_id,
                trace_id=trace_id,
                status=run_status,
                prompt=prompt,
                output=final_output if run_status == "completed" else None,
                error=error_message,
                total_steps=step_count,
                duration_ms=total_duration_ms,
                prompt_tokens=total_prompt_tokens,
                completion_tokens=total_completion_tokens,
                total_tokens=total_tokens,
                estimated_cost=estimated_cost,
                is_synthetic=is_synthetic,
                created_at=start_time,
                completed_at=end_time
            )
            session.add(agent_run)

            trace = Trace(
                id=trace_id,
                project_id=project_id,
                agent_run_id=run_id,
                name=f"{agent_type.capitalize()} Assistant Run",
                status="ok" if run_status == "completed" else "error",
                start_time=start_time,
                end_time=end_time,
                duration_ms=total_duration_ms,
                total_spans=len(collected_spans),
                total_tokens=total_tokens,
                estimated_cost=estimated_cost,
                is_synthetic=is_synthetic,
                created_at=start_time
            )
            session.add(trace)

            for s in collected_spans:
                span_record = Span(
                    id=str(uuid.uuid4()),
                    span_id=s["span_id"],
                    trace_id=trace_id,
                    parent_span_id=s.get("parent_span_id"),
                    name=s["name"],
                    kind=s.get("kind", "INTERNAL"),
                    operation_name=s["operation_name"],
                    status=s.get("status", "ok"),
                    status_message=s.get("status_message"),
                    start_time=s["start_time"],
                    end_time=s.get("end_time"),
                    duration_ms=s.get("duration_ms", 0.0),
                    gen_ai_system=s.get("gen_ai_system"),
                    gen_ai_model=s.get("gen_ai_model"),
                    prompt_tokens=s.get("prompt_tokens", 0),
                    completion_tokens=s.get("completion_tokens", 0),
                    total_tokens=s.get("total_tokens", 0),
                    tool_name=s.get("tool_name"),
                    tool_args=s.get("tool_args"),
                    tool_result=s.get("tool_result"),
                    attributes=s.get("attributes", {}),
                    created_at=start_time
                )
                session.add(span_record)

            await session.commit()
    except Exception as db_err:
        print(f"Error persisting trace to database: {db_err}")

    # Emit final completion event
    summary_data = {
        "run_id": run_id,
        "trace_id": trace_id,
        "status": run_status,
        "duration_ms": total_duration_ms,
        "total_tokens": total_tokens,
        "estimated_cost": estimated_cost,
        "total_steps": step_count
    }
    yield f"event: agent_completed\ndata: {json.dumps(summary_data)}\n\n"


def cancel_agent_run(run_id: str) -> bool:
    """Trigger cooperative cancellation of an active agent execution."""
    if run_id in RUNNING_TASKS:
        RUNNING_TASKS[run_id].set()
        return True
    return False
