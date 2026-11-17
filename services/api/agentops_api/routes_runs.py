"""FastAPI Router for Agent Execution, SSE Streaming & Cancellation."""

from fastapi import APIRouter, Depends, HTTPException, Query, status
from fastapi.responses import StreamingResponse
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from agentops_api.database import get_db
from agentops_api.models import AgentRun, Agent
from agentops_api.schemas import AgentRunRequest, AgentRunResponse, StandardResponse
from agentops_api.agent_runtime import run_agent_workflow, cancel_agent_run
from agentops_api.rate_limiter import rate_limit_dependency

router = APIRouter(prefix="/api/v1/agent-runs", tags=["Agent Execution & Playground"])


@router.post("", dependencies=[Depends(rate_limit_dependency)])
async def execute_agent_run(
    payload: AgentRunRequest,
    project_id: str = Query(..., description="Target project ID"),
    db: AsyncSession = Depends(get_db)
):
    """
    Execute an agent workflow.
    If stream=True (default), returns a real-time Server-Sent Events (SSE) text/event-stream.
    """
    # Resolve agent type & model
    agent_type = "research"
    model = payload.model or "mock-agent-v1"
    
    if payload.agent_id:
        res = await db.execute(select(Agent).where(Agent.id == payload.agent_id))
        agent = res.scalar_one_or_none()
        if agent:
            agent_type = agent.agent_type
            model = payload.model or agent.default_model

    if payload.stream:
        generator = run_agent_workflow(
            project_id=project_id,
            prompt=payload.prompt,
            agent_id=payload.agent_id,
            agent_type=agent_type,
            model=model,
            is_synthetic=False
        )
        return StreamingResponse(
            generator,
            media_type="text/event-stream",
            headers={
                "Cache-Control": "no-cache",
                "Connection": "keep-alive",
                "X-Accel-Buffering": "no"
            }
        )
    else:
        # Non-streaming fallback: consume generator and return final state
        # In practice, stream=True is the primary path for the Playground
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Streaming mode is required for interactive playground. Set stream=true."
        )


@router.post("/{run_id}/cancel", response_model=StandardResponse)
async def cancel_run(run_id: str):
    """Cancel an active in-flight agent run."""
    cancelled = cancel_agent_run(run_id)
    if not cancelled:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Run not found or already completed."
        )
    return StandardResponse(success=True, message=f"Run {run_id} cancelled.")


@router.get("/{run_id}", response_model=AgentRunResponse)
async def get_agent_run(
    run_id: str,
    db: AsyncSession = Depends(get_db)
):
    """Retrieve details and final output of an agent run."""
    query = select(AgentRun).where(AgentRun.id == run_id)
    res = await db.execute(query)
    run = res.scalar_one_or_none()
    if not run:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Agent run not found")
    return run
