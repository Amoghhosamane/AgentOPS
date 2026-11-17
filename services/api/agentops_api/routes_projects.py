"""FastAPI Router for Project, Agent, and API Key Management."""

from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from agentops_api.database import get_db
from agentops_api.models import Project, Agent, AgentVersion, ApiKey, User
from agentops_api.schemas import (
    ProjectCreate,
    ProjectResponse,
    AgentCreate,
    AgentResponse,
    ApiKeyCreate,
    ApiKeyCreatedResponse,
    ApiKeyResponse
)
from agentops_api.auth import (
    get_current_user,
    generate_api_key_pair,
    verify_project_access
)

router = APIRouter(prefix="/api/v1", tags=["Projects & Agents"])


# -------------------------------------------------------------------------
# Projects Endpoints
# -------------------------------------------------------------------------
@router.get("/projects", response_model=List[ProjectResponse])
async def list_projects(
    db: AsyncSession = Depends(get_db)
):
    """List all available projects in current workspace."""
    query = select(Project).order_by(Project.created_at.desc())
    result = await db.execute(query)
    return result.scalars().all()


@router.post("/projects", response_model=ProjectResponse, status_code=status.HTTP_201_CREATED)
async def create_project(
    payload: ProjectCreate,
    db: AsyncSession = Depends(get_db)
):
    """Create a new project environment."""
    # Find default organization
    from agentops_api.models import Organization
    res = await db.execute(select(Organization).limit(1))
    org = res.scalar_one_or_none()
    org_id = org.id if org else "default-org"

    slug = payload.slug or payload.name.lower().replace(" ", "-")
    project = Project(
        name=payload.name,
        slug=slug,
        description=payload.description,
        organization_id=org_id
    )
    db.add(project)
    await db.commit()
    await db.refresh(project)
    return project


# -------------------------------------------------------------------------
# Agents Endpoints
# -------------------------------------------------------------------------
@router.get("/projects/{project_id}/agents", response_model=List[AgentResponse])
async def list_agents(
    project_id: str,
    db: AsyncSession = Depends(get_db)
):
    """List registered agents for a project."""
    query = select(Agent).where(Agent.project_id == project_id).order_by(Agent.created_at.desc())
    result = await db.execute(query)
    return result.scalars().all()


@router.post("/projects/{project_id}/agents", response_model=AgentResponse, status_code=status.HTTP_201_CREATED)
async def create_agent(
    project_id: str,
    payload: AgentCreate,
    db: AsyncSession = Depends(get_db)
):
    """Register an agent within a project."""
    slug = payload.slug or payload.name.lower().replace(" ", "-")
    agent = Agent(
        project_id=project_id,
        name=payload.name,
        slug=slug,
        description=payload.description,
        agent_type=payload.agent_type,
        model_provider=payload.model_provider,
        default_model=payload.default_model,
        system_prompt=payload.system_prompt
    )
    db.add(agent)
    await db.commit()
    await db.refresh(agent)
    return agent


# -------------------------------------------------------------------------
# API Keys Endpoints
# -------------------------------------------------------------------------
@router.get("/projects/{project_id}/api-keys", response_model=List[ApiKeyResponse])
async def list_api_keys(
    project_id: str,
    db: AsyncSession = Depends(get_db)
):
    """List project API keys (hashed values not exposed)."""
    query = select(ApiKey).where(ApiKey.project_id == project_id).order_by(ApiKey.created_at.desc())
    result = await db.execute(query)
    return result.scalars().all()


@router.post("/projects/{project_id}/api-keys", response_model=ApiKeyCreatedResponse, status_code=status.HTTP_201_CREATED)
async def create_api_key(
    project_id: str,
    payload: ApiKeyCreate,
    db: AsyncSession = Depends(get_db)
):
    """Generate a new scoped API key for SDK/OTLP ingestion."""
    raw_key, prefix, hashed = generate_api_key_pair()
    api_key = ApiKey(
        project_id=project_id,
        name=payload.name,
        key_prefix=prefix,
        hashed_key=hashed,
        is_active=True
    )
    db.add(api_key)
    await db.commit()
    await db.refresh(api_key)

    return ApiKeyCreatedResponse(
        id=api_key.id,
        name=api_key.name,
        key_prefix=api_key.key_prefix,
        raw_api_key=raw_key,
        created_at=api_key.created_at
    )
