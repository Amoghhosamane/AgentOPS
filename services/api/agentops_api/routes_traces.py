"""FastAPI Router for Distributed Traces & OpenTelemetry Ingestion."""

import uuid
from datetime import datetime, timezone
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, desc

from agentops_api.database import get_db
from agentops_api.models import Trace, Span, Project, ApiKey
from agentops_api.schemas import (
    TraceListResponse,
    TraceSummaryItem,
    TraceDetailResponse,
    SpanItem,
    OTLPIngestBatch,
    StandardResponse
)
from agentops_api.auth import get_project_by_api_key
from agentops_api.rate_limiter import rate_limit_dependency

router = APIRouter(prefix="/api/v1", tags=["Traces & OpenTelemetry"])


@router.get("/projects/{project_id}/traces", response_model=TraceListResponse)
async def list_traces(
    project_id: str,
    status_filter: Optional[str] = Query(None, alias="status"),
    is_synthetic: Optional[bool] = Query(None),
    page: int = Query(1, ge=1),
    page_size: int = Query(25, ge=1, le=100),
    db: AsyncSession = Depends(get_db)
):
    """Retrieve paginated traces for a project with optional status filter."""
    query = select(Trace).where(Trace.project_id == project_id)
    if status_filter:
        query = query.where(Trace.status == status_filter)
    if is_synthetic is not None:
        query = query.where(Trace.is_synthetic == is_synthetic)

    # Count total
    count_query = select(func.count()).select_from(query.subquery())
    total_count = (await db.execute(count_query)).scalar() or 0

    # Paginate
    query = query.order_by(desc(Trace.created_at)).offset((page - 1) * page_size).limit(page_size)
    result = await db.execute(query)
    traces = result.scalars().all()

    summary_items = [
        TraceSummaryItem(
            id=t.id,
            project_id=t.project_id,
            agent_run_id=t.agent_run_id,
            name=t.name,
            status=t.status,
            start_time=t.start_time,
            duration_ms=t.duration_ms,
            total_spans=t.total_spans,
            total_tokens=t.total_tokens,
            estimated_cost=t.estimated_cost,
            is_synthetic=t.is_synthetic
        )
        for t in traces
    ]

    return TraceListResponse(
        traces=summary_items,
        total=total_count,
        page=page,
        page_size=page_size
    )


@router.get("/traces/{trace_id}", response_model=TraceDetailResponse)
async def get_trace(
    trace_id: str,
    db: AsyncSession = Depends(get_db)
):
    """Get complete waterfall trace with all child OpenTelemetry spans."""
    trace_query = select(Trace).where(Trace.id == trace_id)
    trace_res = await db.execute(trace_query)
    trace = trace_res.scalar_one_or_none()
    if not trace:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Trace not found")

    spans_query = select(Span).where(Span.trace_id == trace_id).order_by(Span.start_time.asc())
    spans_res = await db.execute(spans_query)
    spans = spans_res.scalars().all()

    span_items = [
        SpanItem(
            id=s.id,
            span_id=s.span_id,
            trace_id=s.trace_id,
            parent_span_id=s.parent_span_id,
            name=s.name,
            kind=s.kind,
            operation_name=s.operation_name,
            status=s.status,
            status_message=s.status_message,
            start_time=s.start_time,
            end_time=s.end_time,
            duration_ms=s.duration_ms,
            gen_ai_system=s.gen_ai_system,
            gen_ai_model=s.gen_ai_model,
            prompt_tokens=s.prompt_tokens,
            completion_tokens=s.completion_tokens,
            total_tokens=s.total_tokens,
            tool_name=s.tool_name,
            tool_args=s.tool_args,
            tool_result=s.tool_result,
            attributes=s.attributes or {},
            events=s.events or [],
            created_at=s.created_at
        )
        for s in spans
    ]

    return TraceDetailResponse(
        id=trace.id,
        project_id=trace.project_id,
        agent_run_id=trace.agent_run_id,
        name=trace.name,
        status=trace.status,
        start_time=trace.start_time,
        end_time=trace.end_time,
        duration_ms=trace.duration_ms,
        total_spans=trace.total_spans,
        total_tokens=trace.total_tokens,
        estimated_cost=trace.estimated_cost,
        is_synthetic=trace.is_synthetic,
        created_at=trace.created_at,
        spans=span_items
    )


# -------------------------------------------------------------------------
# OpenTelemetry Ingestion Endpoint
# -------------------------------------------------------------------------
@router.post(
    "/telemetry/v1/traces",
    response_model=StandardResponse,
    dependencies=[Depends(rate_limit_dependency)]
)
async def ingest_otlp_spans(
    payload: OTLPIngestBatch,
    api_project: Optional[Project] = Depends(get_project_by_api_key),
    db: AsyncSession = Depends(get_db)
):
    """
    Ingest OpenTelemetry GenAI spans from the Python SDK or OTLP collector.
    Enforces API key authentication and sliding-window rate limiting.
    """
    if not api_project:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Valid X-AgentOps-Api-Key header required for ingestion."
        )

    if not payload.spans:
        return StandardResponse(success=True, message="Empty span batch received.")

    # Group incoming spans by trace_id
    traces_map = {}
    for s in payload.spans:
        traces_map.setdefault(s.trace_id, []).append(s)

    now = datetime.now(timezone.utc)

    for trace_id, spans in traces_map.items():
        # Check if trace exists or create root trace
        t_res = await db.execute(select(Trace).where(Trace.id == trace_id))
        trace = t_res.scalar_one_or_none()
        
        earliest_start = min(s.start_time_unix_nano for s in spans) / 1e9
        trace_start_dt = datetime.fromtimestamp(earliest_start, tz=timezone.utc)

        if not trace:
            trace = Trace(
                id=trace_id,
                project_id=api_project.id,
                name=spans[0].name,
                status="ok",
                start_time=trace_start_dt,
                duration_ms=0.0,
                total_spans=len(spans),
                total_tokens=0,
                estimated_cost=0.0,
                is_synthetic=False,
                created_at=now
            )
            db.add(trace)
        else:
            trace.total_spans += len(spans)

        for s in spans:
            start_sec = s.start_time_unix_nano / 1e9
            start_dt = datetime.fromtimestamp(start_sec, tz=timezone.utc)
            end_dt = datetime.fromtimestamp(s.end_time_unix_nano / 1e9, tz=timezone.utc) if s.end_time_unix_nano else None
            dur = (s.end_time_unix_nano - s.start_time_unix_nano) / 1e6 if s.end_time_unix_nano else 0.0

            # GenAI convention extraction
            prompt_toks = s.attributes.get("gen_ai.usage.input_tokens", 0)
            comp_toks = s.attributes.get("gen_ai.usage.output_tokens", 0)
            tot_toks = s.attributes.get("gen_ai.usage.total_tokens", prompt_toks + comp_toks)
            model_name = s.attributes.get("gen_ai.request.model") or s.attributes.get("gen_ai.response.model")
            system_name = s.attributes.get("gen_ai.system", "custom")
            tool_name = s.attributes.get("gen_ai.tool.name")

            span_record = Span(
                id=str(uuid.uuid4()),
                span_id=s.span_id,
                trace_id=trace_id,
                parent_span_id=s.parent_span_id,
                name=s.name,
                kind="INTERNAL",
                operation_name=s.attributes.get("gen_ai.operation.name", "unknown"),
                status=s.status or "ok",
                status_message=s.status_message,
                start_time=start_dt,
                end_time=end_dt,
                duration_ms=dur,
                gen_ai_system=system_name,
                gen_ai_model=model_name,
                prompt_tokens=prompt_toks,
                completion_tokens=comp_toks,
                total_tokens=tot_toks,
                tool_name=tool_name,
                attributes=s.attributes,
                events=s.events,
                created_at=now
            )
            db.add(span_record)
            trace.total_tokens += tot_toks

    await db.commit()
    return StandardResponse(success=True, message=f"Ingested {len(payload.spans)} spans successfully.")
