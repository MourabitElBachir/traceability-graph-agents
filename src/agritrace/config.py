"""Environment-backed settings. Defaults run the demo with no API key and no Neo4j."""

from __future__ import annotations

import os
from dataclasses import dataclass
from datetime import date


def _env(name: str, default: str) -> str:
    value = os.getenv(name)
    return default if value is None or value == "" else value


@dataclass(frozen=True)
class Settings:
    """Runtime configuration.

    ``llm_mode=mock`` never calls a network. ``graph_backend=memory`` keeps CI
    independent of Docker. The clock is ``as_of``, not the wall clock, so an
    expired certificate stays expired in tests.
    """

    llm_mode: str
    llm_base_url: str
    llm_api_key: str
    llm_model: str
    embedding_model: str
    embedding_dim: int
    graph_backend: str
    neo4j_uri: str
    neo4j_user: str
    neo4j_password: str
    database_path: str
    otel_exporter: str
    otel_endpoint: str
    as_of: date
    audit_log_path: str
    demo_open_access: bool
    ontology_path: str

    @classmethod
    def from_env(cls) -> Settings:
        return cls(
            llm_mode=_env("LLM_MODE", "mock"),
            llm_base_url=_env("LLM_BASE_URL", "https://api.openai.com/v1").rstrip("/"),
            llm_api_key=_env("LLM_API_KEY", ""),
            llm_model=_env("LLM_MODEL", "gpt-4o-mini"),
            embedding_model=_env("EMBEDDING_MODEL", "text-embedding-3-small"),
            embedding_dim=int(_env("EMBEDDING_DIM", "64")),
            graph_backend=_env("GRAPH_BACKEND", "memory"),
            neo4j_uri=_env("NEO4J_URI", "bolt://localhost:7687"),
            neo4j_user=_env("NEO4J_USER", "neo4j"),
            neo4j_password=_env("NEO4J_PASSWORD", ""),
            database_path=_env("ERP_DATABASE_PATH", "var/erp.sqlite"),
            otel_exporter=_env("OTEL_EXPORTER", "none"),
            otel_endpoint=_env("OTEL_EXPORTER_OTLP_ENDPOINT", ""),
            as_of=date.fromisoformat(_env("AGRITRACE_AS_OF", "2026-11-13")),
            audit_log_path=_env("AUDIT_LOG_PATH", ""),
            demo_open_access=_env("AGRITRACE_DEMO_OPEN", "1") == "1",
            ontology_path=_env("AGRITRACE_ONTOLOGY", ""),
        )


def get_settings() -> Settings:
    return Settings.from_env()
