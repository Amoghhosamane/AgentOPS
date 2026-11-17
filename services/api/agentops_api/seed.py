"""Seed initial demo organization, project, agents, and synthetic traces.

Ensures the platform is immediately useful out-of-the-box while maintaining strict labeling
of synthetic/demonstration records vs live executions.
"""

import uuid
from datetime import datetime, timedelta, timezone
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from agentops_api.models import (
    Organization,
    Project,
    User,
    ApiKey,
    Agent,
    AgentVersion,
    AgentRun,
    Trace,
    Span,
    EvaluationDataset,
    EvaluationCase,
    Alert
)
from agentops_api.auth import hash_password, hash_api_key

DEMO_ORG_ID = "org-agentops-demo-001"
DEMO_PROJECT_ID = "proj-agentops-demo-001"
DEMO_API_KEY_RAW = "aop_live_demo1234567890abcdef"


async def seed_demo_data(session: AsyncSession):
    """Seed initial project, agents, traces, and evaluation datasets if not already present."""
    # Check if demo project exists
    q = select(Project).where(Project.id == DEMO_PROJECT_ID)
    res = await session.execute(q)
    if res.scalar_one_or_none():
        return  # Already seeded

    now = datetime.now(timezone.utc)

    # 1. Organization
    org = Organization(
        id=DEMO_ORG_ID,
        name="Acme AI Technologies",
        slug="acme-ai",
        created_at=now - timedelta(days=30)
    )
    session.add(org)

    # 2. User
    user = User(
        id=str(uuid.uuid4()),
        organization_id=DEMO_ORG_ID,
        email="admin@agentops.ai",
        hashed_password=hash_password("AgentOps2026!"),
        full_name="Principal Engineer",
        role="owner",
        is_active=True,
        created_at=now - timedelta(days=30)
    )
    session.add(user)

    # 3. Project
    project = Project(
        id=DEMO_PROJECT_ID,
        organization_id=DEMO_ORG_ID,
        name="Production Agents",
        slug="production-agents",
        description="Core multi-agent production environment for research and analytical workflows.",
        created_at=now - timedelta(days=30)
    )
    session.add(project)

    # 4. API Key
    api_key = ApiKey(
        id=str(uuid.uuid4()),
        project_id=DEMO_PROJECT_ID,
        name="Default Ingestion Key",
        key_prefix="aop_live_demo",
        hashed_key=hash_api_key(DEMO_API_KEY_RAW),
        is_active=True,
        created_at=now - timedelta(days=30)
    )
    session.add(api_key)

    # 5. Agents
    agent1 = Agent(
        id="agent-research-01",
        project_id=DEMO_PROJECT_ID,
        name="Research Assistant",
        slug="research-assistant",
        description="Autonomous agent for literature review, synthesis, and search retrieval.",
        agent_type="research",
        model_provider="mock",
        default_model="mock-agent-v1",
        system_prompt="You are a meticulous research assistant. Break down queries and cite sources.",
        created_at=now - timedelta(days=15)
    )
    session.add(agent1)

    agent2 = Agent(
        id="agent-analytics-02",
        project_id=DEMO_PROJECT_ID,
        name="Data Analysis Assistant",
        slug="data-analyst",
        description="Structured data processing agent performing statistical aggregation.",
        agent_type="analysis",
        model_provider="mock",
        default_model="mock-agent-v1",
        system_prompt="You are an analytical assistant capable of executing mathematical computations.",
        created_at=now - timedelta(days=15)
    )
    session.add(agent2)

    # 6. Evaluation Dataset & Test Cases
    eval_dataset = EvaluationDataset(
        id="eval-ds-001",
        project_id=DEMO_PROJECT_ID,
        name="Core Capabilities Benchmark",
        description="Standard evaluation suite testing knowledge retrieval, JSON compliance, and tool accuracy.",
        version="1.0.0",
        created_at=now - timedelta(days=10)
    )
    session.add(eval_dataset)

    case1 = EvaluationCase(
        id=str(uuid.uuid4()),
        dataset_id=eval_dataset.id,
        prompt="Explain what OpenTelemetry is in the context of AI agent observability.",
        expected_output="OpenTelemetry provides vendor-neutral APIs and SDKs to instrument traces and metrics.",
        required_keywords=["OpenTelemetry", "observability", "traces"],
        expected_tools=["search_knowledge_base"],
        max_latency_ms=2500.0,
        created_at=now - timedelta(days=10)
    )
    session.add(case1)

    case2 = EvaluationCase(
        id=str(uuid.uuid4()),
        dataset_id=eval_dataset.id,
        prompt="Calculate summary statistics for recent latency measurements.",
        expected_tools=["calculate_statistics"],
        json_schema={"type": "object", "required": ["mean", "count"]},
        max_latency_ms=2000.0,
        created_at=now - timedelta(days=10)
    )
    session.add(case2)

    case3 = EvaluationCase(
        id=str(uuid.uuid4()),
        dataset_id=eval_dataset.id,
        prompt="What is AgentOps and how does it evaluate agent performance?",
        required_keywords=["AgentOps", "evaluation", "benchmarking"],
        expected_tools=["search_knowledge_base"],
        max_latency_ms=3000.0,
        created_at=now - timedelta(days=10)
    )
    session.add(case3)

    # 7. Seed Synthetic Historical Traces (Labeled is_synthetic=True)
    traces_data = [
        ("Query system architecture", 350.0, 180, "ok", agent1.id),
        ("Analyze cluster memory metrics", 480.0, 240, "ok", agent2.id),
        ("Deep retrieval on OpenTelemetry standards", 620.0, 310, "ok", agent1.id),
        ("Calculate rate limit percentiles", 290.0, 150, "ok", agent2.id),
        ("Complex multi-hop search query", 890.0, 420, "ok", agent1.id),
        ("Outbound tool network timeout", 1250.0, 95, "error", agent1.id),
    ]

    for idx, (title, dur, tokens, stat, ag_id) in enumerate(traces_data):
        trace_time = now - timedelta(hours=(idx * 4) + 1)
        t_id = uuid.uuid4().hex
        run_id = str(uuid.uuid4())

        run = AgentRun(
            id=run_id,
            project_id=DEMO_PROJECT_ID,
            agent_id=ag_id,
            trace_id=t_id,
            status="completed" if stat == "ok" else "failed",
            prompt=title,
            output="Executed synthetic baseline workflow." if stat == "ok" else None,
            error="Upstream network socket timeout" if stat == "error" else None,
            total_steps=3,
            duration_ms=dur,
            prompt_tokens=int(tokens * 0.4),
            completion_tokens=int(tokens * 0.6),
            total_tokens=tokens,
            estimated_cost=round((tokens / 1000.0) * 0.0015, 6),
            is_synthetic=True,  # Explicitly labeled!
            created_at=trace_time,
            completed_at=trace_time + timedelta(milliseconds=dur)
        )
        session.add(run)

        trace = Trace(
            id=t_id,
            project_id=DEMO_PROJECT_ID,
            agent_run_id=run_id,
            name=title,
            status=stat,
            start_time=trace_time,
            end_time=trace_time + timedelta(milliseconds=dur),
            duration_ms=dur,
            total_spans=3,
            total_tokens=tokens,
            estimated_cost=round((tokens / 1000.0) * 0.0015, 6),
            is_synthetic=True,
            created_at=trace_time
        )
        session.add(trace)

        # Spans
        root_span_id = uuid.uuid4().hex[:16]
        span1 = Span(
            id=str(uuid.uuid4()),
            span_id=root_span_id,
            trace_id=t_id,
            name="agent.run",
            operation_name="agent.run",
            kind="SERVER",
            status=stat,
            start_time=trace_time,
            end_time=trace_time + timedelta(milliseconds=dur),
            duration_ms=dur,
            gen_ai_system="agentops-synthetic",
            gen_ai_model="mock-agent-v1",
            total_tokens=tokens,
            attributes={"is_synthetic": True},
            created_at=trace_time
        )
        session.add(span1)

        tool_span_id = uuid.uuid4().hex[:16]
        span2 = Span(
            id=str(uuid.uuid4()),
            span_id=tool_span_id,
            trace_id=t_id,
            parent_span_id=root_span_id,
            name="tool.execute",
            operation_name="tool.execute",
            kind="CLIENT",
            status="ok" if stat == "ok" else "error",
            start_time=trace_time + timedelta(milliseconds=50),
            end_time=trace_time + timedelta(milliseconds=dur * 0.5),
            duration_ms=round(dur * 0.45, 2),
            tool_name="search_knowledge_base" if ag_id == agent1.id else "calculate_statistics",
            attributes={"is_synthetic": True},
            created_at=trace_time
        )
        session.add(span2)

    # 8. Seed Alert
    alert = Alert(
        id=str(uuid.uuid4()),
        project_id=DEMO_PROJECT_ID,
        severity="info",
        title="AgentOps Synthetic Demo Loaded",
        message="Standard benchmark datasets, baseline traces, and agents initialized successfully.",
        source="system",
        status="active",
        created_at=now
    )
    session.add(alert)

    await session.commit()
