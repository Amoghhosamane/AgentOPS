"""SQLAlchemy models for AgentOps.

Implements entities for:
- Multi-tenancy (Organizations, Projects, API Keys, Users)
- Agents & Versions
- Conversations & Messages
- Agent Runs, Traces & OpenTelemetry Spans
- Evaluations (Datasets, Test Cases, Evaluation Runs & Results)
- Alerts & Audit Logs
"""

import uuid
from datetime import datetime, timezone
from typing import Optional, List, Dict, Any
from sqlalchemy import (
    Column,
    String,
    Text,
    Boolean,
    Integer,
    Float,
    DateTime,
    ForeignKey,
    Index,
    JSON
)
from sqlalchemy.orm import relationship
from agentops_api.database import Base


def get_utc_now() -> datetime:
    """Return current UTC timestamp with timezone awareness."""
    return datetime.now(timezone.utc)


def generate_uuid() -> str:
    """Generate string representation of standard UUID v4."""
    return str(uuid.uuid4())


class Organization(Base):
    """Organization entity representing a customer account/company."""
    __tablename__ = "organizations"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    name = Column(String(100), nullable=False)
    slug = Column(String(100), unique=True, nullable=False, index=True)
    created_at = Column(DateTime(timezone=True), default=get_utc_now, nullable=False)
    updated_at = Column(DateTime(timezone=True), default=get_utc_now, onupdate=get_utc_now, nullable=False)

    # Relationships
    projects = relationship("Project", back_populates="organization", cascade="all, delete-orphan")
    users = relationship("User", back_populates="organization", cascade="all, delete-orphan")


class User(Base):
    """User entity for authentication and RBAC."""
    __tablename__ = "users"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    organization_id = Column(String(36), ForeignKey("organizations.id", ondelete="CASCADE"), nullable=False, index=True)
    email = Column(String(255), unique=True, nullable=False, index=True)
    hashed_password = Column(String(255), nullable=False)
    full_name = Column(String(100), nullable=False)
    role = Column(String(20), default="member", nullable=False)  # owner, admin, member, viewer
    is_active = Column(Boolean, default=True, nullable=False)
    created_at = Column(DateTime(timezone=True), default=get_utc_now, nullable=False)

    # Relationships
    organization = relationship("Organization", back_populates="users")


class Project(Base):
    """Project entity representing an environment or agent application namespace."""
    __tablename__ = "projects"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    organization_id = Column(String(36), ForeignKey("organizations.id", ondelete="CASCADE"), nullable=False, index=True)
    name = Column(String(100), nullable=False)
    slug = Column(String(100), nullable=False, index=True)
    description = Column(Text, nullable=True)
    created_at = Column(DateTime(timezone=True), default=get_utc_now, nullable=False)
    updated_at = Column(DateTime(timezone=True), default=get_utc_now, onupdate=get_utc_now, nullable=False)

    # Relationships
    organization = relationship("Organization", back_populates="projects")
    api_keys = relationship("ApiKey", back_populates="project", cascade="all, delete-orphan")
    agents = relationship("Agent", back_populates="project", cascade="all, delete-orphan")
    traces = relationship("Trace", back_populates="project", cascade="all, delete-orphan")
    agent_runs = relationship("AgentRun", back_populates="project", cascade="all, delete-orphan")
    eval_datasets = relationship("EvaluationDataset", back_populates="project", cascade="all, delete-orphan")
    alerts = relationship("Alert", back_populates="project", cascade="all, delete-orphan")


class ApiKey(Base):
    """API Key for authenticating SDK and OTLP ingestion."""
    __tablename__ = "api_keys"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    project_id = Column(String(36), ForeignKey("projects.id", ondelete="CASCADE"), nullable=False, index=True)
    name = Column(String(100), nullable=False)
    key_prefix = Column(String(12), nullable=False)  # e.g., 'aop_live_abc'
    hashed_key = Column(String(64), nullable=False, unique=True, index=True)  # SHA-256 hash
    is_active = Column(Boolean, default=True, nullable=False)
    last_used_at = Column(DateTime(timezone=True), nullable=True)
    created_at = Column(DateTime(timezone=True), default=get_utc_now, nullable=False)

    # Relationships
    project = relationship("Project", back_populates="api_keys")


class Agent(Base):
    """Agent entity registered within a project."""
    __tablename__ = "agents"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    project_id = Column(String(36), ForeignKey("projects.id", ondelete="CASCADE"), nullable=False, index=True)
    name = Column(String(100), nullable=False)
    slug = Column(String(100), nullable=False, index=True)
    description = Column(Text, nullable=True)
    agent_type = Column(String(50), default="chat", nullable=False)  # research, analysis, chat, custom
    model_provider = Column(String(50), default="mock", nullable=False)  # openai, anthropic, mock
    default_model = Column(String(100), default="mock-agent-v1", nullable=False)
    system_prompt = Column(Text, nullable=True)
    created_at = Column(DateTime(timezone=True), default=get_utc_now, nullable=False)
    updated_at = Column(DateTime(timezone=True), default=get_utc_now, onupdate=get_utc_now, nullable=False)

    # Relationships
    project = relationship("Project", back_populates="agents")
    versions = relationship("AgentVersion", back_populates="agent", cascade="all, delete-orphan")
    runs = relationship("AgentRun", back_populates="agent", cascade="all, delete-orphan")


class AgentVersion(Base):
    """Versioned snapshot of an agent prompt, configuration, and tools."""
    __tablename__ = "agent_versions"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    agent_id = Column(String(36), ForeignKey("agents.id", ondelete="CASCADE"), nullable=False, index=True)
    version = Column(String(50), nullable=False)  # e.g., '1.0.0', '1.1.0'
    system_prompt = Column(Text, nullable=True)
    model = Column(String(100), nullable=False)
    temperature = Column(Float, default=0.7, nullable=False)
    tools_config = Column(JSON, default=list, nullable=False)
    metadata_json = Column(JSON, default=dict, nullable=False)
    created_at = Column(DateTime(timezone=True), default=get_utc_now, nullable=False)

    # Relationships
    agent = relationship("Agent", back_populates="versions")


class Conversation(Base):
    """Conversation thread grouping multiple agent messages in the playground."""
    __tablename__ = "conversations"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    project_id = Column(String(36), ForeignKey("projects.id", ondelete="CASCADE"), nullable=False, index=True)
    agent_id = Column(String(36), ForeignKey("agents.id", ondelete="CASCADE"), nullable=False, index=True)
    title = Column(String(200), default="New Chat", nullable=False)
    created_at = Column(DateTime(timezone=True), default=get_utc_now, nullable=False)
    updated_at = Column(DateTime(timezone=True), default=get_utc_now, onupdate=get_utc_now, nullable=False)

    # Relationships
    messages = relationship("Message", back_populates="conversation", cascade="all, delete-orphan", order_by="Message.created_at")


class Message(Base):
    """Single message within a playground conversation."""
    __tablename__ = "messages"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    conversation_id = Column(String(36), ForeignKey("conversations.id", ondelete="CASCADE"), nullable=False, index=True)
    role = Column(String(20), nullable=False)  # user, assistant, system, tool
    content = Column(Text, nullable=False)
    tool_calls = Column(JSON, nullable=True)
    trace_id = Column(String(64), nullable=True, index=True)
    agent_run_id = Column(String(36), nullable=True, index=True)
    created_at = Column(DateTime(timezone=True), default=get_utc_now, nullable=False)

    # Relationships
    conversation = relationship("Conversation", back_populates="messages")


class AgentRun(Base):
    """High-level execution record of an agent run."""
    __tablename__ = "agent_runs"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    project_id = Column(String(36), ForeignKey("projects.id", ondelete="CASCADE"), nullable=False, index=True)
    agent_id = Column(String(36), ForeignKey("agents.id", ondelete="SET NULL"), nullable=True, index=True)
    trace_id = Column(String(64), nullable=False, index=True)
    status = Column(String(20), default="running", nullable=False)  # running, completed, failed, cancelled
    prompt = Column(Text, nullable=False)
    output = Column(Text, nullable=True)
    error = Column(Text, nullable=True)
    total_steps = Column(Integer, default=0, nullable=False)
    duration_ms = Column(Float, default=0.0, nullable=False)
    prompt_tokens = Column(Integer, default=0, nullable=False)
    completion_tokens = Column(Integer, default=0, nullable=False)
    total_tokens = Column(Integer, default=0, nullable=False)
    estimated_cost = Column(Float, default=0.0, nullable=False)
    is_synthetic = Column(Boolean, default=False, nullable=False)
    created_at = Column(DateTime(timezone=True), default=get_utc_now, nullable=False)
    completed_at = Column(DateTime(timezone=True), nullable=True)

    # Relationships
    project = relationship("Project", back_populates="agent_runs")
    agent = relationship("Agent", back_populates="runs")
    trace = relationship("Trace", back_populates="agent_run", uselist=False)

    __table_args__ = (
        Index("ix_agent_runs_project_created", "project_id", "created_at"),
        Index("ix_agent_runs_status", "status"),
    )


class Trace(Base):
    """Distributed Trace grouping parent-child spans for an agent execution."""
    __tablename__ = "traces"

    id = Column(String(64), primary_key=True)  # Standard 32-char hex or UUID
    project_id = Column(String(36), ForeignKey("projects.id", ondelete="CASCADE"), nullable=False, index=True)
    agent_run_id = Column(String(36), ForeignKey("agent_runs.id", ondelete="SET NULL"), nullable=True, index=True)
    name = Column(String(150), nullable=False)
    status = Column(String(20), default="ok", nullable=False)  # ok, error, unset
    start_time = Column(DateTime(timezone=True), nullable=False)
    end_time = Column(DateTime(timezone=True), nullable=True)
    duration_ms = Column(Float, default=0.0, nullable=False)
    total_spans = Column(Integer, default=1, nullable=False)
    total_tokens = Column(Integer, default=0, nullable=False)
    estimated_cost = Column(Float, default=0.0, nullable=False)
    is_synthetic = Column(Boolean, default=False, nullable=False)
    created_at = Column(DateTime(timezone=True), default=get_utc_now, nullable=False)

    # Relationships
    project = relationship("Project", back_populates="traces")
    agent_run = relationship("AgentRun", back_populates="trace")
    spans = relationship("Span", back_populates="trace", cascade="all, delete-orphan", order_by="Span.start_time")

    __table_args__ = (
        Index("ix_traces_project_created", "project_id", "created_at"),
    )


class Span(Base):
    """OpenTelemetry-compliant Span representing an individual operation."""
    __tablename__ = "spans"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    span_id = Column(String(64), nullable=False, index=True)  # OTel 16-char hex or UUID
    trace_id = Column(String(64), ForeignKey("traces.id", ondelete="CASCADE"), nullable=False, index=True)
    parent_span_id = Column(String(64), nullable=True, index=True)
    name = Column(String(150), nullable=False)
    kind = Column(String(50), default="INTERNAL", nullable=False)  # CLIENT, SERVER, INTERNAL
    operation_name = Column(String(100), nullable=False)  # agent.run, chat, tool.execute
    status = Column(String(20), default="ok", nullable=False)  # ok, error
    status_message = Column(Text, nullable=True)
    start_time = Column(DateTime(timezone=True), nullable=False)
    end_time = Column(DateTime(timezone=True), nullable=True)
    duration_ms = Column(Float, default=0.0, nullable=False)
    
    # GenAI Semantic Attributes
    gen_ai_system = Column(String(50), nullable=True)  # openai, anthropic, agentops
    gen_ai_model = Column(String(100), nullable=True)
    prompt_tokens = Column(Integer, default=0, nullable=False)
    completion_tokens = Column(Integer, default=0, nullable=False)
    total_tokens = Column(Integer, default=0, nullable=False)
    
    # Input/Output & Tool Attributes
    tool_name = Column(String(100), nullable=True)
    tool_args = Column(JSON, nullable=True)
    tool_result = Column(JSON, nullable=True)
    attributes = Column(JSON, default=dict, nullable=False)
    events = Column(JSON, default=list, nullable=False)  # OTel Span Events
    created_at = Column(DateTime(timezone=True), default=get_utc_now, nullable=False)

    # Relationships
    trace = relationship("Trace", back_populates="spans")

    __table_args__ = (
        Index("ix_spans_trace_span", "trace_id", "span_id"),
        Index("ix_spans_operation", "operation_name"),
    )


class EvaluationDataset(Base):
    """Versioned dataset of test prompts and ground truth for agent evaluation."""
    __tablename__ = "evaluation_datasets"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    project_id = Column(String(36), ForeignKey("projects.id", ondelete="CASCADE"), nullable=False, index=True)
    name = Column(String(100), nullable=False)
    description = Column(Text, nullable=True)
    version = Column(String(50), default="1.0.0", nullable=False)
    created_at = Column(DateTime(timezone=True), default=get_utc_now, nullable=False)
    updated_at = Column(DateTime(timezone=True), default=get_utc_now, onupdate=get_utc_now, nullable=False)

    # Relationships
    project = relationship("Project", back_populates="eval_datasets")
    test_cases = relationship("EvaluationCase", back_populates="dataset", cascade="all, delete-orphan")
    runs = relationship("EvaluationRun", back_populates="dataset", cascade="all, delete-orphan")


class EvaluationCase(Base):
    """Single test case within an evaluation dataset."""
    __tablename__ = "evaluation_cases"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    dataset_id = Column(String(36), ForeignKey("evaluation_datasets.id", ondelete="CASCADE"), nullable=False, index=True)
    prompt = Column(Text, nullable=False)
    expected_output = Column(Text, nullable=True)
    required_keywords = Column(JSON, default=list, nullable=False)
    expected_tools = Column(JSON, default=list, nullable=False)
    json_schema = Column(JSON, nullable=True)
    max_latency_ms = Column(Float, nullable=True)
    created_at = Column(DateTime(timezone=True), default=get_utc_now, nullable=False)

    # Relationships
    dataset = relationship("EvaluationDataset", back_populates="test_cases")


class EvaluationRun(Base):
    """Execution run of an evaluation dataset against a specific agent version."""
    __tablename__ = "evaluation_runs"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    project_id = Column(String(36), ForeignKey("projects.id", ondelete="CASCADE"), nullable=False, index=True)
    dataset_id = Column(String(36), ForeignKey("evaluation_datasets.id", ondelete="CASCADE"), nullable=False, index=True)
    agent_id = Column(String(36), ForeignKey("agents.id", ondelete="SET NULL"), nullable=True, index=True)
    agent_version = Column(String(50), default="latest", nullable=False)
    status = Column(String(20), default="pending", nullable=False)  # pending, running, completed, failed
    total_cases = Column(Integer, default=0, nullable=False)
    passed_cases = Column(Integer, default=0, nullable=False)
    failed_cases = Column(Integer, default=0, nullable=False)
    pass_rate = Column(Float, default=0.0, nullable=False)  # Percentage 0.0 - 100.0
    average_latency_ms = Column(Float, default=0.0, nullable=False)
    total_tokens = Column(Integer, default=0, nullable=False)
    created_at = Column(DateTime(timezone=True), default=get_utc_now, nullable=False)
    completed_at = Column(DateTime(timezone=True), nullable=True)

    # Relationships
    dataset = relationship("EvaluationDataset", back_populates="runs")
    results = relationship("EvaluationResult", back_populates="run", cascade="all, delete-orphan")


class EvaluationResult(Base):
    """Result of evaluating a single test case in an evaluation run."""
    __tablename__ = "evaluation_results"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    run_id = Column(String(36), ForeignKey("evaluation_runs.id", ondelete="CASCADE"), nullable=False, index=True)
    case_id = Column(String(36), ForeignKey("evaluation_cases.id", ondelete="SET NULL"), nullable=True, index=True)
    trace_id = Column(String(64), nullable=True, index=True)
    status = Column(String(20), default="passed", nullable=False)  # passed, failed, error
    actual_output = Column(Text, nullable=True)
    latency_ms = Column(Float, default=0.0, nullable=False)
    scores = Column(JSON, default=dict, nullable=False)  # e.g., {"exact_match": 1.0, "json_validity": 1.0, "tool_accuracy": 0.8}
    reasons = Column(JSON, default=list, nullable=False)
    created_at = Column(DateTime(timezone=True), default=get_utc_now, nullable=False)

    # Relationships
    run = relationship("EvaluationRun", back_populates="results")


class Alert(Base):
    """Alert triggered by rate limits, error spikes, or latency thresholds."""
    __tablename__ = "alerts"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    project_id = Column(String(36), ForeignKey("projects.id", ondelete="CASCADE"), nullable=False, index=True)
    severity = Column(String(20), default="warning", nullable=False)  # info, warning, error, critical
    title = Column(String(150), nullable=False)
    message = Column(Text, nullable=False)
    source = Column(String(50), default="system", nullable=False)  # rate_limit, agent_error, eval_failure
    status = Column(String(20), default="active", nullable=False)  # active, resolved, acknowledged
    created_at = Column(DateTime(timezone=True), default=get_utc_now, nullable=False)
    resolved_at = Column(DateTime(timezone=True), nullable=True)

    # Relationships
    project = relationship("Project", back_populates="alerts")


class AuditLog(Base):
    """Immutable audit trail of administrative and mutation actions."""
    __tablename__ = "audit_logs"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    project_id = Column(String(36), nullable=False, index=True)
    user_id = Column(String(36), nullable=True)
    action = Column(String(100), nullable=False)  # api_key.create, agent.delete, project.update
    resource_type = Column(String(50), nullable=False)
    resource_id = Column(String(64), nullable=False)
    details = Column(JSON, default=dict, nullable=False)
    created_at = Column(DateTime(timezone=True), default=get_utc_now, nullable=False)
