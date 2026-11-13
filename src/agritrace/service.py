"""One front door for the API, the CLI, MCP tools, and the A2A example."""

from __future__ import annotations

from typing import Any

from langgraph.types import Command

from agritrace.agents.graph import build_agent
from agritrace.config import Settings, get_settings
from agritrace.data.erp import roundtrip
from agritrace.data.generator import build_dataset
from agritrace.data.quality import QualityReport, check_quality
from agritrace.graph.memory import MemoryStore
from agritrace.llm.provider import LLMClient, build_llm
from agritrace.models import AskResponse, Citation
from agritrace.observability.otel import configure_telemetry, start_span
from agritrace.retrieval.embeddings import HashEmbedder, OpenAIEmbedder
from agritrace.retrieval.text_to_cypher import draft_cypher
from agritrace.security.audit_log import AuditLog
from agritrace.security.rbac import (
    AccessDenied,
    Principal,
    principal_for_actor,
    regulator,
    require_lot,
    require_tool,
    tool_allowed,
)


def _embedder(settings: Settings) -> HashEmbedder | OpenAIEmbedder:
    if settings.llm_mode == "openai":
        return OpenAIEmbedder(
            settings.llm_base_url,
            settings.llm_api_key,
            settings.embedding_model,
            settings.embedding_dim,
        )
    return HashEmbedder(settings.embedding_dim)


def _interrupted(snapshot: Any) -> bool:
    interrupts = getattr(snapshot, "interrupts", None)
    if interrupts:
        return True
    for task in getattr(snapshot, "tasks", ()) or ():
        if getattr(task, "interrupts", None):
            return True
    return False


class TraceService:
    def __init__(self, settings: Settings, store: MemoryStore, llm: LLMClient, quality: QualityReport) -> None:
        self.settings = settings
        self.store = store
        self.llm = llm
        self.quality = quality
        self.audit = AuditLog(settings.audit_log_path)
        self.graph = build_agent(store, llm, settings.as_of.isoformat())

    def default_principal(self) -> Principal:
        if self.settings.demo_open_access:
            return regulator()
        raise AccessDenied("Set X-Actor-Id. Demo open access is disabled.")

    def principal_from_actor(self, actor_id: str | None) -> Principal:
        if not actor_id:
            return self.default_principal()
        if actor_id == "regulator":
            return regulator()
        return principal_for_actor(self.store.require_index().dataset, actor_id)

    def ask(
        self,
        question: str,
        thread_id: str,
        principal: Principal | None = None,
        human_decision: str | None = None,
    ) -> AskResponse:
        caller = principal or self.default_principal()
        config = {"configurable": {"thread_id": thread_id}}
        with start_span("agent.ask", route="pending", **{"enduser.role": caller.role}):
            if human_decision is not None:
                self.graph.invoke(Command(resume=human_decision), config)
            else:
                self.graph.invoke(
                    {
                        "question": question,
                        "principal": caller.as_dict(),
                        "status": "running",
                        "citations": [],
                        "injection_flags": [],
                        "documents": [],
                    },
                    config,
                )
        snapshot = self.graph.get_state(config)
        values: dict[str, Any] = dict(snapshot.values or {})
        status = "needs_approval" if _interrupted(snapshot) else str(values.get("status") or "complete")
        if status not in {"complete", "needs_approval", "denied"}:
            status = "complete"
        cypher: dict[str, Any] | None = None
        if human_decision is None and tool_allowed(caller.role, "read_cypher") and status != "denied":
            cypher = self._cypher(question, caller)
        citations = [Citation.model_validate(row) for row in values.get("citations") or []]
        event = self.audit.record(
            action="ask" if human_decision is None else "resume_recall",
            allowed=status != "denied",
            principal_role=caller.role,
            principal_actor_id=caller.actor_id,
            question=question,
            human_decision=human_decision,
            route=values.get("route"),
            status=status,
            lot_id=values.get("lot_id"),
            injection_flags=values.get("injection_flags") or [],
        )
        return AskResponse(
            status=status,  # type: ignore[arg-type]
            route=str(values.get("route") or ""),
            answer=str(values.get("answer") or ""),
            citations=citations,
            recall_proposal=values.get("recall_proposal"),
            cypher=cypher,
            principal=caller.as_dict(),
            injection_flags=list(values.get("injection_flags") or []),
            audit_event_id=str(event["id"]),
            thread_id=thread_id,
        )

    def trace(self, lot_id: str, direction: str, principal: Principal | None = None) -> dict[str, Any]:
        caller = principal or self.default_principal()
        with start_span("graph.trace", **{"lot.id": lot_id}):
            try:
                require_tool(caller, "trace_lot")
                require_lot(self.store.require_index(), caller, lot_id)
            except AccessDenied as exc:
                self.audit.record(
                    action="trace_lot",
                    allowed=False,
                    principal_role=caller.role,
                    principal_actor_id=caller.actor_id,
                    lot_id=lot_id,
                    detail=str(exc),
                )
                raise
            result = self.store.trace(lot_id, direction)
        self.audit.record(
            action="trace_lot",
            allowed=True,
            principal_role=caller.role,
            principal_actor_id=caller.actor_id,
            lot_id=lot_id,
        )
        return result

    def check(self, lot_id: str, principal: Principal | None = None) -> dict[str, Any]:
        caller = principal or self.default_principal()
        with start_span("graph.compliance", **{"lot.id": lot_id}):
            require_tool(caller, "check_certificates")
            require_lot(self.store.require_index(), caller, lot_id)
            return self.store.check_lot(lot_id, self.settings.as_of)

    def search(self, query: str, k: int = 4, principal: Principal | None = None) -> list[dict[str, Any]]:
        caller = principal or self.default_principal()
        require_tool(caller, "search_documents")
        from agritrace.agents.graph import _visible_chunk
        from agritrace.security.rbac import visible_lots

        with start_span("retrieval.search"):
            allowed = visible_lots(self.store.require_index(), caller)
            hits = [hit for hit in self.store.search(query, k=max(k * 2, 8)) if _visible_chunk(hit, allowed, caller)]
        self.audit.record(
            action="search_documents",
            allowed=True,
            principal_role=caller.role,
            principal_actor_id=caller.actor_id,
            detail=query[:240],
        )
        return hits[:k]

    def read_cypher(self, cypher: str, params: dict[str, str], principal: Principal | None = None) -> dict[str, Any]:
        caller = principal or self.default_principal()
        try:
            require_tool(caller, "read_cypher")
        except AccessDenied as exc:
            self.audit.record(
                action="read_cypher",
                allowed=False,
                principal_role=caller.role,
                principal_actor_id=caller.actor_id,
                detail=str(exc),
            )
            raise
        from agritrace.security.cypher_guard import validate_cypher

        safe = validate_cypher(cypher)
        rows = self._filter_rows(self.store.run_read_cypher(safe, params), caller)
        self.audit.record(
            action="read_cypher",
            allowed=True,
            principal_role=caller.role,
            principal_actor_id=caller.actor_id,
            detail=safe[:240],
        )
        return {"cypher": safe, "rows": rows}

    def _cypher(self, question: str, caller: Principal) -> dict[str, Any]:
        drafted = draft_cypher(question, self.llm, self.settings.as_of.isoformat())
        if not drafted.get("ok"):
            return drafted
        raw_params = drafted.get("params")
        params = {str(key): str(value) for key, value in raw_params.items()} if isinstance(raw_params, dict) else {}
        rows = self._filter_rows(self.store.run_read_cypher(str(drafted["cypher"]), params), caller)
        return {**drafted, "rows": rows}

    def _filter_rows(self, rows: list[dict[str, str]], caller: Principal) -> list[dict[str, str]]:
        from agritrace.security.rbac import visible_lots

        allowed = visible_lots(self.store.require_index(), caller)
        kept: list[dict[str, str]] = []
        for row in rows:
            lot_values = [
                row.get("lot_id"),
                row.get("origin_lot"),
                row.get("wheat"),
                row.get("flour"),
                row.get("biscuits"),
            ]
            hidden = [value for value in lot_values if value and value not in allowed]
            if not hidden:
                kept.append(row)
        return kept


def build_service(settings: Settings | None = None) -> TraceService:
    """Quality-check the fictional world, round-trip it through SQL, then load the graph."""

    settings = settings or get_settings()
    configure_telemetry(settings.otel_exporter, settings.otel_endpoint)
    dataset = build_dataset()
    quality = check_quality(dataset)
    if not quality.ok:
        raise RuntimeError("data quality failed: " + "; ".join(quality.errors))
    with start_span("ingest.sql_to_graph", backend=settings.graph_backend):
        loaded = roundtrip(dataset, ":memory:")
        store = MemoryStore(_embedder(settings))
        store.load(loaded)
        if settings.graph_backend == "neo4j":
            from agritrace.graph.neo4j_store import Neo4jStore

            Neo4jStore(settings, store).sync()
    return TraceService(settings, store, build_llm(settings), quality)
