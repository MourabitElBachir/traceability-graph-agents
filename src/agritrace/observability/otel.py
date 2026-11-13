"""Spans around ingestion, retrieval, and agent turns.

LangSmith stays optional: set LANGCHAIN_TRACING_V2=true and LANGCHAIN_API_KEY
and the LangChain / LangGraph callbacks pick it up. This module does not send
data anywhere by default.
"""

from __future__ import annotations

from collections.abc import Iterator
from contextlib import contextmanager
from typing import Any

from opentelemetry import trace
from opentelemetry.sdk.resources import Resource
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import BatchSpanProcessor, ConsoleSpanExporter

_CONFIGURED = False


def configure_telemetry(exporter: str = "none", endpoint: str = "") -> None:
    global _CONFIGURED
    if _CONFIGURED:
        return
    provider = TracerProvider(resource=Resource.create({"service.name": "agritrace"}))
    if exporter == "console":
        provider.add_span_processor(BatchSpanProcessor(ConsoleSpanExporter()))
    elif exporter == "otlp" and endpoint:
        from opentelemetry.exporter.otlp.proto.http.trace_exporter import OTLPSpanExporter

        provider.add_span_processor(BatchSpanProcessor(OTLPSpanExporter(endpoint=endpoint)))
    trace.set_tracer_provider(provider)
    _CONFIGURED = True


@contextmanager
def start_span(name: str, **attributes: Any) -> Iterator[Any]:
    tracer = trace.get_tracer("agritrace")
    with tracer.start_as_current_span(name) as span:
        for key, value in attributes.items():
            if value is not None:
                span.set_attribute(key, value)
        yield span
