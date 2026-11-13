"""Shared demo service. Mock LLM, memory graph, fixed clock."""

from __future__ import annotations

import os

os.environ.setdefault("LLM_MODE", "mock")
os.environ.setdefault("GRAPH_BACKEND", "memory")
os.environ.setdefault("OTEL_EXPORTER", "none")
os.environ.setdefault("AUDIT_LOG_PATH", "")
os.environ.setdefault("AGRITRACE_AS_OF", "2026-11-13")
os.environ.setdefault("AGRITRACE_DEMO_OPEN", "1")

import pytest

from agritrace.service import TraceService, build_service


@pytest.fixture(scope="session")
def engine() -> TraceService:
    return build_service()
