"""Pydantic v2 schemas for AgentOps API."""

from datetime import datetime
from typing import List, Optional, Dict, Any, Union
from pydantic import BaseModel, Field, EmailStr, ConfigDict


# -------------------------------------------------------------------------
# Base / Common Schemas
# -------------------------------------------------------------------------
class StandardResponse(BaseModel):
    success: bool = True
    message: Optional[str] = None


class ApiErrorDetail(BaseModel):
    code: str
    message: str
    details: Optional[Any] = None


class ApiErrorResponse(BaseModel):
    error: ApiErrorDetail


# -------------------------------------------------------------------------
# Auth & User Schemas
# -------------------------------------------------------------------------
class UserBase(BaseModel):
    email: EmailStr
    full_name: str
    role: str = "member"


class UserCreate(UserBase):
    password: str
    organization_name: Optional[str] = "Default Organization"


class UserResponse(UserBase):
    id: str
    organization_id: str
    is_active: bool
    created_at: datetime
    model_config = ConfigDict(from_attributes=True)


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user: UserResponse


class LoginRequest(BaseModel):
    email: EmailStr
    password: str


# -------------------------------------------------------------------------
# Organization & Project Schemas
# -------------------------------------------------------------------------
class OrganizationResponse(BaseModel):
    id: str
    name: str
    slug: str
    created_at: datetime
    model_config = ConfigDict(from_attributes=True)


class ProjectCreate(BaseModel):
    name: str = Field(..., min_length=2, max_length=100)
    slug: Optional[str] = None
    description: Optional[str] = None


class ProjectResponse(BaseModel):
    id: str
    organization_id: str
    name: str
    slug: str
    description: Optional[str] = None
    created_at: datetime
    updated_at: datetime
    model_config = ConfigDict(from_attributes=True)


class ApiKeyCreate(BaseModel):
    name: str = Field(..., min_length=2, max_length=100)


class ApiKeyCreatedResponse(BaseModel):
    id: str
    name: str
    key_prefix: str
    raw_api_key: str  # Only returned upon creation!
    created_at: datetime


class ApiKeyResponse(BaseModel):
    id: str
    name: str
    key_prefix: str
    is_active: bool
    last_used_at: Optional[datetime] = None
    created_at: datetime
    model_config = ConfigDict(from_attributes=True)


# -------------------------------------------------------------------------
# Agent & Version Schemas
# -------------------------------------------------------------------------
class AgentCreate(BaseModel):
    name: str = Field(..., min_length=2, max_length=100)
    slug: Optional[str] = None
    description: Optional[str] = None
    agent_type: str = "chat"  # research, analysis, chat
    model_provider: str = "mock"  # mock, openai, anthropic
    default_model: str = "mock-agent-v1"
    system_prompt: Optional[str] = "You are a helpful and meticulous AI Assistant."


class AgentResponse(BaseModel):
    id: str
    project_id: str
    name: str
    slug: str
    description: Optional[str] = None
    agent_type: str
    model_provider: str
    default_model: str
    system_prompt: Optional[str] = None
    created_at: datetime
    updated_at: datetime
    model_config = ConfigDict(from_attributes=True)


class AgentVersionCreate(BaseModel):
    version: str = Field(..., pattern=r"^\d+\.\d+\.\d+$")
    system_prompt: Optional[str] = None
    model: str
    temperature: float = 0.7
    tools_config: List[Dict[str, Any]] = []
    metadata_json: Dict[str, Any] = {}


class AgentVersionResponse(BaseModel):
    id: str
    agent_id: str
    version: str
    system_prompt: Optional[str] = None
    model: str
    temperature: float
    tools_config: List[Dict[str, Any]]
    metadata_json: Dict[str, Any]
    created_at: datetime
    model_config = ConfigDict(from_attributes=True)


# -------------------------------------------------------------------------
# Agent Playground & Execution Schemas
# -------------------------------------------------------------------------
class AgentRunRequest(BaseModel):
    agent_id: Optional[str] = None
    prompt: str = Field(..., min_length=1)
    conversation_id: Optional[str] = None
    stream: bool = True
    provider: Optional[str] = "mock"  # mock, openai, anthropic
    model: Optional[str] = None


class AgentRunStep(BaseModel):
    step_number: int
    step_type: str  # thought, tool_call, tool_result, output
    content: Optional[str] = None
    tool_name: Optional[str] = None
    tool_args: Optional[Dict[str, Any]] = None
    tool_result: Optional[Any] = None
    duration_ms: float = 0.0


class AgentRunResponse(BaseModel):
    id: str
    project_id: str
    agent_id: Optional[str] = None
    trace_id: str
    status: str
    prompt: str
    output: Optional[str] = None
    error: Optional[str] = None
    total_steps: int
    duration_ms: float
    prompt_tokens: int
    completion_tokens: int
    total_tokens: int
    estimated_cost: float
    is_synthetic: bool
    created_at: datetime
    completed_at: Optional[datetime] = None
    model_config = ConfigDict(from_attributes=True)


# -------------------------------------------------------------------------
# Traces & OpenTelemetry Spans
# -------------------------------------------------------------------------
class SpanItem(BaseModel):
    id: str
    span_id: str
    trace_id: str
    parent_span_id: Optional[str] = None
    name: str
    kind: str
    operation_name: str
    status: str
    status_message: Optional[str] = None
    start_time: datetime
    end_time: Optional[datetime] = None
    duration_ms: float
    gen_ai_system: Optional[str] = None
    gen_ai_model: Optional[str] = None
    prompt_tokens: int = 0
    completion_tokens: int = 0
    total_tokens: int = 0
    tool_name: Optional[str] = None
    tool_args: Optional[Dict[str, Any]] = None
    tool_result: Optional[Any] = None
    attributes: Dict[str, Any] = {}
    events: List[Dict[str, Any]] = []
    created_at: datetime
    model_config = ConfigDict(from_attributes=True)


class TraceDetailResponse(BaseModel):
    id: str
    project_id: str
    agent_run_id: Optional[str] = None
    name: str
    status: str
    start_time: datetime
    end_time: Optional[datetime] = None
    duration_ms: float
    total_spans: int
    total_tokens: int
    estimated_cost: float
    is_synthetic: bool
    created_at: datetime
    spans: List[SpanItem] = []
    model_config = ConfigDict(from_attributes=True)


class TraceSummaryItem(BaseModel):
    id: str
    project_id: str
    agent_run_id: Optional[str] = None
    name: str
    status: str
    start_time: datetime
    duration_ms: float
    total_spans: int
    total_tokens: int
    estimated_cost: float
    is_synthetic: bool
    model_config = ConfigDict(from_attributes=True)


class TraceListResponse(BaseModel):
    traces: List[TraceSummaryItem]
    total: int
    page: int
    page_size: int


# -------------------------------------------------------------------------
# OTLP Ingestion Schemas
# -------------------------------------------------------------------------
class OTLPSpanIngest(BaseModel):
    trace_id: str
    span_id: str
    parent_span_id: Optional[str] = None
    name: str
    start_time_unix_nano: int
    end_time_unix_nano: Optional[int] = None
    status: Optional[str] = "ok"
    status_message: Optional[str] = None
    attributes: Dict[str, Any] = {}
    events: List[Dict[str, Any]] = []


class OTLPIngestBatch(BaseModel):
    spans: List[OTLPSpanIngest]


# -------------------------------------------------------------------------
# Evaluation Schemas
# -------------------------------------------------------------------------
class EvaluationCaseCreate(BaseModel):
    prompt: str
    expected_output: Optional[str] = None
    required_keywords: List[str] = []
    expected_tools: List[str] = []
    json_schema: Optional[Dict[str, Any]] = None
    max_latency_ms: Optional[float] = None


class EvaluationCaseResponse(EvaluationCaseCreate):
    id: str
    dataset_id: str
    created_at: datetime
    model_config = ConfigDict(from_attributes=True)


class EvaluationDatasetCreate(BaseModel):
    name: str = Field(..., min_length=2, max_length=100)
    description: Optional[str] = None
    version: str = "1.0.0"
    test_cases: List[EvaluationCaseCreate] = []


class EvaluationDatasetResponse(BaseModel):
    id: str
    project_id: str
    name: str
    description: Optional[str] = None
    version: str
    created_at: datetime
    updated_at: datetime
    test_cases: List[EvaluationCaseResponse] = []
    model_config = ConfigDict(from_attributes=True)


class EvaluationRunCreate(BaseModel):
    dataset_id: str
    agent_id: Optional[str] = None
    agent_version: str = "latest"


class EvaluationResultItem(BaseModel):
    id: str
    run_id: str
    case_id: Optional[str] = None
    trace_id: Optional[str] = None
    status: str
    actual_output: Optional[str] = None
    latency_ms: float
    scores: Dict[str, float]
    reasons: List[str]
    created_at: datetime
    model_config = ConfigDict(from_attributes=True)


class EvaluationRunResponse(BaseModel):
    id: str
    project_id: str
    dataset_id: str
    agent_id: Optional[str] = None
    agent_version: str
    status: str
    total_cases: int
    passed_cases: int
    failed_cases: int
    pass_rate: float
    average_latency_ms: float
    total_tokens: int
    created_at: datetime
    completed_at: Optional[datetime] = None
    results: List[EvaluationResultItem] = []
    model_config = ConfigDict(from_attributes=True)


# -------------------------------------------------------------------------
# Metrics & Overview Schemas
# -------------------------------------------------------------------------
class MetricsOverviewResponse(BaseModel):
    total_agent_runs: int
    success_rate: float  # Percentage
    p95_latency_ms: float
    total_tokens: int
    estimated_cost: float
    eval_pass_rate: float
    runs_over_time: List[Dict[str, Any]]
    tokens_by_model: List[Dict[str, Any]]
    errors_by_category: List[Dict[str, Any]]
    latency_percentiles: Dict[str, float]


class AlertResponse(BaseModel):
    id: str
    project_id: str
    severity: str
    title: str
    message: str
    source: str
    status: str
    created_at: datetime
    resolved_at: Optional[datetime] = None
    model_config = ConfigDict(from_attributes=True)
