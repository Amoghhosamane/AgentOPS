"""AgentOps Python SDK.

Provides clean OpenTelemetry-compliant instrumentation for customer AI agents:
- Client initialization with endpoint and project API key.
- Context-managed Traces and Spans.
- Model call token tracking following GenAI semantic conventions.
- Tool invocation durations and outputs.
- Batched OTLP span flushing.
"""

import time
import uuid
import httpx
from typing import Dict, Any, List, Optional
from contextlib import contextmanager


class SpanRecorder:
    """Represents an active span during agent execution."""

    def __init__(self, tracer: 'AgentOpsTracer', name: str, operation_name: str, parent_span_id: Optional[str] = None):
        self.tracer = tracer
        self.name = name
        self.operation_name = operation_name
        self.span_id = uuid.uuid4().hex[:16]
        self.parent_span_id = parent_span_id
        self.start_time_nano = int(time.time() * 1e9)
        self.end_time_nano: Optional[int] = None
        self.status = "ok"
        self.status_message: Optional[str] = None
        self.attributes: Dict[str, Any] = {"gen_ai.operation.name": operation_name}
        self.events: List[Dict[str, Any]] = []

    def set_attribute(self, key: str, value: Any):
        self.attributes[key] = value

    def set_tokens(self, input_tokens: int, output_tokens: int):
        self.attributes["gen_ai.usage.input_tokens"] = input_tokens
        self.attributes["gen_ai.usage.output_tokens"] = output_tokens
        self.attributes["gen_ai.usage.total_tokens"] = input_tokens + output_tokens

    def set_model(self, model: str, system: str = "openai"):
        self.attributes["gen_ai.request.model"] = model
        self.attributes["gen_ai.response.model"] = model
        self.attributes["gen_ai.system"] = system

    def record_error(self, message: str):
        self.status = "error"
        self.status_message = message

    def finish(self):
        self.end_time_nano = int(time.time() * 1e9)
        self.tracer._record_span(self)


class AgentOpsTracer:
    """Client for recording and exporting agent traces to AgentOps platform."""

    def __init__(self, api_key: str, endpoint: str = "http://localhost:8000"):
        self.api_key = api_key
        self.endpoint = endpoint.rstrip("/")
        self.trace_id = uuid.uuid4().hex
        self._spans: List[SpanRecorder] = []
        self._current_span_id: Optional[str] = None

    @contextmanager
    def start_span(self, name: str, operation_name: str = "chat"):
        """Context manager to record a span."""
        parent_id = self._current_span_id
        span = SpanRecorder(self, name=name, operation_name=operation_name, parent_span_id=parent_id)
        prev_span_id = self._current_span_id
        self._current_span_id = span.span_id
        try:
            yield span
        except Exception as e:
            span.record_error(str(e))
            raise
        finally:
            span.finish()
            self._current_span_id = prev_span_id

    def _record_span(self, span: SpanRecorder):
        self._spans.append(span)

    def flush(self) -> bool:
        """Send recorded spans to AgentOps API."""
        if not self._spans:
            return True

        payload = {
            "spans": [
                {
                    "trace_id": self.trace_id,
                    "span_id": s.span_id,
                    "parent_span_id": s.parent_span_id,
                    "name": s.name,
                    "start_time_unix_nano": s.start_time_nano,
                    "end_time_unix_nano": s.end_time_nano,
                    "status": s.status,
                    "status_message": s.status_message,
                    "attributes": s.attributes,
                    "events": s.events
                }
                for s in self._spans
            ]
        }

        try:
            headers = {"X-AgentOps-Api-Key": self.api_key}
            with httpx.Client(timeout=5.0) as client:
                res = client.post(f"{self.endpoint}/api/v1/telemetry/v1/traces", json=payload, headers=headers)
                return res.status_code == 200
        except Exception as err:
            print(f"Failed to flush spans: {err}")
            return False


class AgentOps:
    """Main entrypoint for customer instrumentation."""
    
    _api_key: Optional[str] = None
    _endpoint: str = "http://localhost:8000"

    @classmethod
    def init(cls, api_key: str, endpoint: str = "http://localhost:8000"):
        cls._api_key = api_key
        cls._endpoint = endpoint

    @classmethod
    def start_trace(cls) -> AgentOpsTracer:
        if not cls._api_key:
            raise ValueError("AgentOps.init(api_key=...) must be called prior to starting a trace.")
        return AgentOpsTracer(api_key=cls._api_key, endpoint=cls._endpoint)
