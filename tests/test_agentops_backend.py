"""Comprehensive test suite for AgentOps API."""

import pytest
import pytest_asyncio
import uuid
import httpx
from agentops_api.main import app
from agentops_api.database import init_db, get_db_context
from agentops_api.seed import seed_demo_data, DEMO_PROJECT_ID, DEMO_API_KEY_RAW
from agentops_api.eval_engine import EvaluationEngine
from agentops_api.models import EvaluationCase


@pytest_asyncio.fixture(autouse=True)
async def setup_database():
    """Ensure database tables and demo seed are present before tests run."""
    await init_db()
    async with get_db_context() as session:
        await seed_demo_data(session)


@pytest.mark.asyncio
async def test_health_probes():
    """Verify liveness and readiness endpoints."""
    async with httpx.AsyncClient(transport=httpx.ASGITransport(app=app), base_url="http://test") as client:
        res_live = await client.get("/health/live")
        assert res_live.status_code == 200
        assert res_live.json()["status"] == "ok"

        res_ready = await client.get("/health/ready")
        assert res_ready.status_code == 200
        assert res_ready.json()["database"] == "connected"


@pytest.mark.asyncio
async def test_projects_and_agents_api():
    """Verify listing and creating projects and agents."""
    async with httpx.AsyncClient(transport=httpx.ASGITransport(app=app), base_url="http://test") as client:
        # List projects
        res = await client.get("/api/v1/projects")
        assert res.status_code == 200
        projects = res.json()
        assert len(projects) >= 1
        assert any(p["id"] == DEMO_PROJECT_ID for p in projects)

        # List agents
        res_agents = await client.get(f"/api/v1/projects/{DEMO_PROJECT_ID}/agents")
        assert res_agents.status_code == 200
        agents = res_agents.json()
        assert len(agents) >= 2
        agent_names = [a["name"] for a in agents]
        assert "Research Assistant" in agent_names
        assert "Data Analysis Assistant" in agent_names


@pytest.mark.asyncio
async def test_agent_run_sse_streaming():
    """Verify Server-Sent Events (SSE) streaming during agent execution."""
    async with httpx.AsyncClient(transport=httpx.ASGITransport(app=app), base_url="http://test") as client:
        payload = {
            "prompt": "Analyze latency metrics for database cluster",
            "stream": True,
            "provider": "mock"
        }
        res = await client.post(
            f"/api/v1/agent-runs?project_id={DEMO_PROJECT_ID}",
            json=payload
        )
        assert res.status_code == 200
        assert "text/event-stream" in res.headers["content-type"]
        
        body = res.text
        assert "event: agent_started" in body
        assert "event: step_started" in body
        assert "event: tool_executing" in body
        assert "event: tool_result" in body
        assert "event: token" in body
        assert "event: agent_completed" in body


@pytest.mark.asyncio
async def test_otlp_telemetry_ingestion_and_waterfall():
    """Verify OpenTelemetry span ingestion and trace retrieval."""
    trace_id = uuid.uuid4().hex
    span_id = uuid.uuid4().hex[:16]
    
    payload = {
        "spans": [
            {
                "trace_id": trace_id,
                "span_id": span_id,
                "name": "chat.completion",
                "start_time_unix_nano": 1700000000000000000,
                "end_time_unix_nano": 1700000000250000000,
                "status": "ok",
                "attributes": {
                    "gen_ai.system": "openai",
                    "gen_ai.request.model": "gpt-4o",
                    "gen_ai.usage.input_tokens": 150,
                    "gen_ai.usage.output_tokens": 75,
                    "gen_ai.operation.name": "chat"
                }
            }
        ]
    }

    async with httpx.AsyncClient(transport=httpx.ASGITransport(app=app), base_url="http://test") as client:
        # Ingestion requires X-AgentOps-Api-Key
        headers = {"X-AgentOps-Api-Key": DEMO_API_KEY_RAW}
        res_ingest = await client.post(
            "/api/v1/telemetry/v1/traces",
            json=payload,
            headers=headers
        )
        assert res_ingest.status_code == 200
        assert res_ingest.json()["success"] is True

        # Retrieve trace details
        res_trace = await client.get(f"/api/v1/traces/{trace_id}")
        assert res_trace.status_code == 200
        trace_data = res_trace.json()
        assert trace_data["id"] == trace_id
        assert len(trace_data["spans"]) >= 1
        assert trace_data["spans"][0]["gen_ai_model"] == "gpt-4o"
        assert trace_data["spans"][0]["total_tokens"] == 225


@pytest.mark.asyncio
async def test_evaluation_engine_and_runs():
    """Verify automated evaluation rules and dataset execution."""
    async with httpx.AsyncClient(transport=httpx.ASGITransport(app=app), base_url="http://test") as client:
        # List datasets
        res_ds = await client.get(f"/api/v1/projects/{DEMO_PROJECT_ID}/evaluations/datasets")
        assert res_ds.status_code == 200
        datasets = res_ds.json()
        assert len(datasets) >= 1
        ds_id = datasets[0]["id"]

        # Trigger evaluation run
        run_payload = {
            "dataset_id": ds_id,
            "agent_version": "1.0.0"
        }
        res_run = await client.post(
            f"/api/v1/projects/{DEMO_PROJECT_ID}/evaluations/runs",
            json=run_payload
        )
        assert res_run.status_code == 201
        run_data = res_run.json()
        assert run_data["status"] == "completed"
        assert run_data["total_cases"] >= 3
        assert run_data["pass_rate"] > 0
        assert len(run_data["results"]) == run_data["total_cases"]


@pytest.mark.asyncio
async def test_rate_limiting():
    """Verify rate limiter blocks when threshold exceeded."""
    from agentops_api.rate_limiter import limiter
    test_id = "test-rate-limit-client"
    await limiter.reset(test_id)

    # Allow up to 3 requests
    allowed1, _, _ = await limiter.check_rate_limit(test_id, max_requests=3, window_seconds=60)
    allowed2, _, _ = await limiter.check_rate_limit(test_id, max_requests=3, window_seconds=60)
    allowed3, _, _ = await limiter.check_rate_limit(test_id, max_requests=3, window_seconds=60)
    assert allowed1 and allowed2 and allowed3

    # 4th request must be rejected with retry-after
    allowed4, remaining, retry_after = await limiter.check_rate_limit(test_id, max_requests=3, window_seconds=60)
    assert not allowed4
    assert remaining == 0
    assert retry_after > 0


@pytest.mark.asyncio
async def test_metrics_overview_accuracy():
    """Verify metrics calculation matches real database telemetry."""
    async with httpx.AsyncClient(transport=httpx.ASGITransport(app=app), base_url="http://test") as client:
        res = await client.get(f"/api/v1/projects/{DEMO_PROJECT_ID}/metrics/overview")
        assert res.status_code == 200
        data = res.json()
        assert data["total_agent_runs"] >= 6
        assert data["success_rate"] >= 50.0
        assert data["p95_latency_ms"] > 0
        assert len(data["runs_over_time"]) >= 1
