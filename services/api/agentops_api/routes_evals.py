"""FastAPI Router for Agent Evaluation Datasets & Benchmark Runs."""

import uuid
from datetime import datetime, timezone
from typing import List
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from agentops_api.database import get_db
from agentops_api.models import (
    EvaluationDataset,
    EvaluationCase,
    EvaluationRun,
    EvaluationResult
)
from agentops_api.schemas import (
    EvaluationDatasetCreate,
    EvaluationDatasetResponse,
    EvaluationCaseResponse,
    EvaluationRunCreate,
    EvaluationRunResponse,
    EvaluationResultItem
)
from agentops_api.eval_engine import EvaluationEngine

router = APIRouter(prefix="/api/v1", tags=["Evaluations & Benchmarks"])


@router.get("/projects/{project_id}/evaluations/datasets", response_model=List[EvaluationDatasetResponse])
async def list_evaluation_datasets(
    project_id: str,
    db: AsyncSession = Depends(get_db)
):
    """List evaluation datasets for a project."""
    query = (
        select(EvaluationDataset)
        .where(EvaluationDataset.project_id == project_id)
        .order_by(EvaluationDataset.created_at.desc())
    )
    result = await db.execute(query)
    datasets = result.scalars().all()

    # Load test cases explicitly into response schemas
    out = []
    for d in datasets:
        cq = select(EvaluationCase).where(EvaluationCase.dataset_id == d.id)
        c_res = await db.execute(cq)
        cases = c_res.scalars().all()
        out.append(
            EvaluationDatasetResponse(
                id=d.id,
                project_id=d.project_id,
                name=d.name,
                description=d.description,
                version=d.version,
                created_at=d.created_at,
                updated_at=d.updated_at,
                test_cases=[
                    EvaluationCaseResponse.model_validate(c) for c in cases
                ]
            )
        )
    return out


@router.post("/projects/{project_id}/evaluations/datasets", response_model=EvaluationDatasetResponse, status_code=status.HTTP_201_CREATED)
async def create_evaluation_dataset(
    project_id: str,
    payload: EvaluationDatasetCreate,
    db: AsyncSession = Depends(get_db)
):
    """Create a versioned evaluation dataset with test cases."""
    dataset = EvaluationDataset(
        project_id=project_id,
        name=payload.name,
        description=payload.description,
        version=payload.version
    )
    db.add(dataset)
    await db.flush()

    cases = []
    for tc in payload.test_cases:
        case = EvaluationCase(
            id=str(uuid.uuid4()),
            dataset_id=dataset.id,
            prompt=tc.prompt,
            expected_output=tc.expected_output,
            required_keywords=tc.required_keywords,
            expected_tools=tc.expected_tools,
            json_schema=tc.json_schema,
            max_latency_ms=tc.max_latency_ms
        )
        db.add(case)
        cases.append(case)

    await db.commit()
    await db.refresh(dataset)
    dataset.test_cases = cases
    return dataset


@router.post("/projects/{project_id}/evaluations/runs", response_model=EvaluationRunResponse, status_code=status.HTTP_201_CREATED)
async def trigger_evaluation_run(
    project_id: str,
    payload: EvaluationRunCreate,
    db: AsyncSession = Depends(get_db)
):
    """Trigger an evaluation run of a dataset against an agent."""
    run_id = str(uuid.uuid4())
    eval_run = EvaluationRun(
        id=run_id,
        project_id=project_id,
        dataset_id=payload.dataset_id,
        agent_id=payload.agent_id,
        agent_version=payload.agent_version,
        status="pending"
    )
    db.add(eval_run)
    await db.commit()

    # Execute evaluation synchronously/inline for instant reproducible feedback
    completed_run = await EvaluationEngine.execute_evaluation_run(
        db=db,
        run_id=run_id,
        dataset_id=payload.dataset_id,
        agent_id=payload.agent_id
    )

    # Fetch results explicitly into response schema
    rq = select(EvaluationResult).where(EvaluationResult.run_id == completed_run.id)
    r_res = await db.execute(rq)
    results = r_res.scalars().all()

    return EvaluationRunResponse(
        id=completed_run.id,
        project_id=completed_run.project_id,
        dataset_id=completed_run.dataset_id,
        agent_id=completed_run.agent_id,
        agent_version=completed_run.agent_version,
        status=completed_run.status,
        total_cases=completed_run.total_cases,
        passed_cases=completed_run.passed_cases,
        failed_cases=completed_run.failed_cases,
        pass_rate=completed_run.pass_rate,
        average_latency_ms=completed_run.average_latency_ms,
        total_tokens=completed_run.total_tokens,
        created_at=completed_run.created_at,
        completed_at=completed_run.completed_at,
        results=[EvaluationResultItem.model_validate(r) for r in results]
    )


@router.get("/projects/{project_id}/evaluations/runs", response_model=List[EvaluationRunResponse])
async def list_evaluation_runs(
    project_id: str,
    db: AsyncSession = Depends(get_db)
):
    """List historical evaluation runs for a project."""
    query = (
        select(EvaluationRun)
        .where(EvaluationRun.project_id == project_id)
        .order_by(EvaluationRun.created_at.desc())
    )
    result = await db.execute(query)
    runs = result.scalars().all()
    
    out = []
    for r in runs:
        rq = select(EvaluationResult).where(EvaluationResult.run_id == r.id)
        r_res = await db.execute(rq)
        results = r_res.scalars().all()
        out.append(
            EvaluationRunResponse(
                id=r.id,
                project_id=r.project_id,
                dataset_id=r.dataset_id,
                agent_id=r.agent_id,
                agent_version=r.agent_version,
                status=r.status,
                total_cases=r.total_cases,
                passed_cases=r.passed_cases,
                failed_cases=r.failed_cases,
                pass_rate=r.pass_rate,
                average_latency_ms=r.average_latency_ms,
                total_tokens=r.total_tokens,
                created_at=r.created_at,
                completed_at=r.completed_at,
                results=[EvaluationResultItem.model_validate(res) for res in results]
            )
        )
    return out
