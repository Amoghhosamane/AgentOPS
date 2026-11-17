"""FastAPI Application Entry Point for AgentOps Platform."""

from contextlib import asynccontextmanager
from fastapi import FastAPI, Request, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from agentops_api.config import settings
from agentops_api.database import init_db, get_db_context
from agentops_api.seed import seed_demo_data
from agentops_api.routes_projects import router as projects_router
from agentops_api.routes_runs import router as runs_router
from agentops_api.routes_traces import router as traces_router
from agentops_api.routes_evals import router as evals_router
from agentops_api.routes_metrics import router as metrics_router


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application startup and shutdown hooks."""
    # 1. Initialize DB tables
    await init_db()
    # 2. Seed initial demo dataset and agents
    async with get_db_context() as session:
        await seed_demo_data(session)
    yield


app = FastAPI(
    title=settings.APP_NAME,
    version=settings.APP_VERSION,
    description="Production-grade AI Agent Observability, Tracing, Monitoring, and Evaluation SaaS Platform.",
    lifespan=lifespan,
    docs_url="/docs",
    redoc_url="/redoc"
)

# CORS Configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include Modular Routers
app.include_router(projects_router)
app.include_router(runs_router)
app.include_router(traces_router)
app.include_router(evals_router)
app.include_router(metrics_router)


# -------------------------------------------------------------------------
# Health Probes
# -------------------------------------------------------------------------
@app.get("/health/live", tags=["Health"])
async def liveness_probe():
    """Liveness probe indicating process is responsive."""
    return {"status": "ok", "service": "agentops-api", "version": settings.APP_VERSION}


@app.get("/health/ready", tags=["Health"])
async def readiness_probe():
    """Readiness probe verifying database connectivity."""
    try:
        async with get_db_context() as session:
            from sqlalchemy import text
            await session.execute(text("SELECT 1"))
        return {"status": "ready", "database": "connected"}
    except Exception as e:
        return JSONResponse(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            content={"status": "degraded", "database": str(e)}
        )
