"""Security and Cross-Tenant Isolation Tests for AgentOps."""

import pytest
import pytest_asyncio
import uuid
import httpx
from agentops_api.main import app
from agentops_api.database import init_db, get_db_context
from agentops_api.seed import seed_demo_data, DEMO_PROJECT_ID, DEMO_API_KEY_RAW
from agentops_api.models import Project, ApiKey
from agentops_api.auth import generate_api_key_pair


@pytest_asyncio.fixture(autouse=True)
async def setup():
    await init_db()
    async with get_db_context() as session:
        await seed_demo_data(session)


@pytest.mark.asyncio
async def test_unauthorized_telemetry_ingest_rejected():
    """Verify OTLP ingestion rejects requests with missing or invalid API keys."""
    async with httpx.AsyncClient(transport=httpx.ASGITransport(app=app), base_url="http://test") as client:
        payload = {"spans": []}
        
        # 1. Missing header
        res_no_key = await client.post("/api/v1/telemetry/v1/traces", json=payload)
        assert res_no_key.status_code == 401

        # 2. Invalid fake key
        res_bad_key = await client.post(
            "/api/v1/telemetry/v1/traces",
            json=payload,
            headers={"X-AgentOps-Api-Key": "aop_live_invalidkey123456789"}
        )
        assert res_bad_key.status_code == 401


@pytest.mark.asyncio
async def test_tenant_api_key_scoping():
    """
    Verify that an API key for Project A cannot ingest or access Project B data.
    """
    async with httpx.AsyncClient(transport=httpx.ASGITransport(app=app), base_url="http://test") as client:
        # Create Project B
        res_b = await client.post("/api/v1/projects", json={"name": "Tenant B Project"})
        assert res_b.status_code == 201
        proj_b_id = res_b.json()["id"]

        # Generate API key specifically for Project B
        res_key_b = await client.post(
            f"/api/v1/projects/{proj_b_id}/api-keys",
            json={"name": "Key B"}
        )
        assert res_key_b.status_code == 201
        raw_key_b = res_key_b.json()["raw_api_key"]

        # Ingest trace using Key B
        trace_b_id = uuid.uuid4().hex
        payload_b = {
            "spans": [
                {
                    "trace_id": trace_b_id,
                    "span_id": uuid.uuid4().hex[:16],
                    "name": "isolated_operation",
                    "start_time_unix_nano": 1700000000000000000,
                    "attributes": {"gen_ai.operation.name": "chat"}
                }
            ]
        }
        res_ingest = await client.post(
            "/api/v1/telemetry/v1/traces",
            json=payload_b,
            headers={"X-AgentOps-Api-Key": raw_key_b}
        )
        assert res_ingest.status_code == 200

        # Query Project A's trace list -> Trace B must NOT appear in Project A's list
        res_traces_a = await client.get(f"/api/v1/projects/{DEMO_PROJECT_ID}/traces")
        assert res_traces_a.status_code == 200
        trace_ids_a = [t["id"] for t in res_traces_a.json()["traces"]]
        assert trace_b_id not in trace_ids_a

        # Query Project B's trace list -> Trace B must be present
        res_traces_b = await client.get(f"/api/v1/projects/{proj_b_id}/traces")
        assert res_traces_b.status_code == 200
        trace_ids_b = [t["id"] for t in res_traces_b.json()["traces"]]
        assert trace_b_id in trace_ids_b
