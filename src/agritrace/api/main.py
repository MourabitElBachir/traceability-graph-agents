"""FastAPI surface. Bind to 0.0.0.0 and $PORT so a container platform can route to it."""

from __future__ import annotations

import os
from typing import Any

from fastapi import FastAPI, Header, HTTPException
from pydantic import BaseModel, Field

from agritrace.a2a.card import agent_card
from agritrace.ontology.loader import summarise
from agritrace.security.rbac import AccessDenied
from agritrace.service import TraceService, build_service

app = FastAPI(
    title="AgriTrace",
    version="0.1.0",
    summary="Fictional agrifood traceability graph, GraphRAG, and multi-agent recall assistant.",
)


class AskBody(BaseModel):
    question: str = Field(examples=["Trace BIS-031 upstream"])
    thread_id: str = "demo"
    actor_id: str | None = None


class ResumeBody(BaseModel):
    thread_id: str
    human_decision: str = Field(pattern="^(approve|reject)$")
    actor_id: str | None = None


class CypherBody(BaseModel):
    cypher: str
    params: dict[str, str] = Field(default_factory=dict)
    actor_id: str | None = None


def _service() -> TraceService:
    if not hasattr(app.state, "service"):
        app.state.service = build_service()
    service: TraceService = app.state.service
    return service


def _principal(service: TraceService, actor_id: str | None) -> Any:
    try:
        return service.principal_from_actor(actor_id)
    except AccessDenied as exc:
        raise HTTPException(status_code=401, detail=str(exc)) from exc
    except StopIteration as exc:
        raise HTTPException(status_code=404, detail="unknown actor") from exc


@app.get("/health")
def health() -> dict[str, Any]:
    service = _service()
    stats = service.store.stats()
    return {
        "status": "ok",
        "llm_mode": service.settings.llm_mode,
        "graph_backend": service.settings.graph_backend,
        "as_of": service.settings.as_of.isoformat(),
        "counts": stats,
        "hero": {"wheat": "BLE-0457", "flour": "FAR-118", "biscuits": "BIS-031", "certificate": "CERT-77"},
    }


@app.get("/ontology")
def ontology() -> dict[str, object]:
    return summarise()


@app.get("/governance/quality")
def quality() -> dict[str, object]:
    service = _service()
    return {"ok": service.quality.ok, "errors": service.quality.errors, "findings": service.quality.findings}


@app.get("/audit")
def audit_events() -> dict[str, object]:
    return {"events": _service().audit.events}


@app.post("/ask")
def ask(body: AskBody, x_actor_id: str | None = Header(default=None)) -> dict[str, Any]:
    service = _service()
    actor = body.actor_id or x_actor_id
    result = service.ask(body.question, body.thread_id, _principal(service, actor))
    return result.model_dump()


@app.post("/ask/resume")
def resume(body: ResumeBody, x_actor_id: str | None = Header(default=None)) -> dict[str, Any]:
    service = _service()
    actor = body.actor_id or x_actor_id
    try:
        result = service.ask("", body.thread_id, _principal(service, actor), body.human_decision)
    except Exception as exc:
        raise HTTPException(status_code=409, detail=str(exc)) from exc
    return result.model_dump()


@app.get("/lots/{lot_id}/trace")
def trace_lot(lot_id: str, direction: str = "both", x_actor_id: str | None = Header(default=None)) -> dict[str, Any]:
    service = _service()
    try:
        return service.trace(lot_id, direction, _principal(service, x_actor_id))
    except AccessDenied as exc:
        raise HTTPException(status_code=403, detail=str(exc)) from exc
    except KeyError as exc:
        raise HTTPException(status_code=404, detail=f"unknown lot {lot_id}") from exc


@app.get("/lots/{lot_id}/compliance")
def check_lot(lot_id: str, x_actor_id: str | None = Header(default=None)) -> dict[str, Any]:
    service = _service()
    try:
        return service.check(lot_id, _principal(service, x_actor_id))
    except AccessDenied as exc:
        raise HTTPException(status_code=403, detail=str(exc)) from exc
    except KeyError as exc:
        raise HTTPException(status_code=404, detail=f"unknown lot {lot_id}") from exc


@app.get("/documents/search")
def search_documents(q: str, k: int = 4, x_actor_id: str | None = Header(default=None)) -> dict[str, Any]:
    service = _service()
    try:
        return {"hits": service.search(q, k, _principal(service, x_actor_id))}
    except AccessDenied as exc:
        raise HTTPException(status_code=403, detail=str(exc)) from exc


@app.post("/cypher")
def cypher(body: CypherBody, x_actor_id: str | None = Header(default=None)) -> dict[str, Any]:
    service = _service()
    from agritrace.security.cypher_guard import CypherRejected

    try:
        return service.read_cypher(body.cypher, body.params, _principal(service, body.actor_id or x_actor_id))
    except AccessDenied as exc:
        raise HTTPException(status_code=403, detail=str(exc)) from exc
    except CypherRejected as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@app.get("/.well-known/agent-card.json")
def well_known_agent(base_url: str = "http://127.0.0.1:8000") -> dict[str, Any]:
    return agent_card(base_url)


@app.post("/a2a/tasks")
def a2a_task(body: dict[str, Any]) -> dict[str, Any]:
    """Minimal A2A-style task endpoint. Labelled as a teaching subset, not a full protocol stack."""

    message = body.get("message") or {}
    parts = message.get("parts") or []
    text = ""
    for part in parts:
        if isinstance(part, dict) and part.get("type") == "text":
            text = str(part.get("text") or "")
            break
    if not text:
        text = str(body.get("text") or "")
    service = _service()
    task_id = str(body.get("id") or "a2a-task")
    result = service.ask(text, thread_id=f"a2a-{task_id}")
    return {
        "protocol": "a2a-minimal-0.1",
        "id": task_id,
        "status": result.status,
        "message": {"role": "agent", "parts": [{"type": "text", "text": result.answer}]},
        "citations": [row.model_dump() for row in result.citations],
    }


def main() -> None:
    import uvicorn

    port = int(os.environ.get("PORT", "8000"))
    uvicorn.run(app, host="0.0.0.0", port=port)
