"""Supervisor graph: route, specialist, and a human interrupt before a recall is issued."""

from __future__ import annotations

from typing import Any, TypedDict

from langgraph.checkpoint.memory import MemorySaver
from langgraph.graph import END, StateGraph
from langgraph.types import interrupt

from agritrace.agents.answers import (
    citations_for_compliance,
    citations_for_documents,
    citations_for_trace,
    render_compliance,
    render_documents,
    render_recall_final,
    render_recall_pending,
    render_trace,
)
from agritrace.agents.router import route_question
from agritrace.graph.memory import MemoryStore
from agritrace.llm.provider import LLMClient
from agritrace.security.guardrails import injection_flags, ungrounded_ids
from agritrace.security.rbac import (
    AccessDenied,
    Principal,
    require_lot,
    require_tool,
    visible_lots,
)


class GraphState(TypedDict, total=False):
    question: str
    route: str
    lot_id: str | None
    direction: str
    certificate_id: str | None
    principal: dict[str, Any]
    trace: dict[str, Any] | None
    compliance: dict[str, Any] | None
    documents: list[dict[str, Any]]
    citations: list[dict[str, str]]
    recall_proposal: dict[str, Any] | None
    human_decision: str | None
    approval_note: str
    answer: str
    status: str
    injection_flags: list[str]


def _principal(state: GraphState) -> Principal:
    raw = state.get("principal") or {}
    role = str(raw.get("role") or "regulator")
    actor_id = raw.get("actor_id")
    name = str(raw.get("name") or role)
    return Principal(role, None if actor_id in {None, ""} else str(actor_id), name)  # type: ignore[arg-type]


def _visible_chunk(hit: dict[str, Any], allowed_lots: set[str], principal: Principal) -> bool:
    if principal.role in {"regulator", "auditor"}:
        return True
    mentioned = [
        entity for entity in hit.get("entity_ids") or [] if str(entity).startswith(("BLE-", "FAR-", "BIS-", "OIL-"))
    ]
    return bool(mentioned) and all(entity in allowed_lots for entity in mentioned)


def build_agent(store: MemoryStore, llm: LLMClient, as_of: str) -> Any:
    """Compile the supervisor. The checkpointer keeps the recall thread until resume."""

    index_holder = store

    def route_node(state: GraphState) -> dict[str, Any]:
        question = state.get("question") or ""
        flags = injection_flags(question)
        decision = route_question(question)
        principal = _principal(state)
        index = index_holder.require_index()
        if decision.lot_id:
            try:
                require_lot(index, principal, decision.lot_id)
            except AccessDenied:
                return {
                    "route": "denied",
                    "status": "denied",
                    "lot_id": decision.lot_id,
                    "direction": decision.direction,
                    "certificate_id": decision.certificate_id,
                    "injection_flags": flags,
                    "answer": (
                        f"Access denied for {principal.role} {principal.actor_id or 'anonymous'} on {decision.lot_id}."
                    ),
                    "citations": [],
                }
        return {
            "route": decision.route,
            "lot_id": decision.lot_id,
            "direction": decision.direction,
            "certificate_id": decision.certificate_id,
            "injection_flags": flags,
            "status": "running",
        }

    def trace_node(state: GraphState) -> dict[str, Any]:
        lot_id = state.get("lot_id")
        if not lot_id:
            return {"trace": None}
        require_tool(_principal(state), "trace_lot")
        return {"trace": store.trace(lot_id, state.get("direction") or "both")}

    def compliance_node(state: GraphState) -> dict[str, Any]:
        principal = _principal(state)
        require_tool(principal, "check_certificates")
        from datetime import date

        clock = date.fromisoformat(as_of)
        lot_id = state.get("lot_id")
        certificate_id = state.get("certificate_id")
        if lot_id:
            report = store.check_lot(lot_id, clock)
            report["mode"] = "lot"
            return {"compliance": report}
        if certificate_id:
            scope = store.certificate(certificate_id)
            scope["mode"] = "certificate"
            return {"compliance": scope}
        return {"compliance": {"mode": "expired", "as_of": as_of, "rows": store.expired(clock)}}

    def documents_node(state: GraphState) -> dict[str, Any]:
        principal = _principal(state)
        require_tool(principal, "search_documents")
        allowed = visible_lots(store.require_index(), principal)
        hits = [
            hit for hit in store.search(state.get("question") or "", k=8) if _visible_chunk(hit, allowed, principal)
        ][:4]
        return {"documents": hits}

    def recall_node(state: GraphState) -> dict[str, Any]:
        lot_id = state.get("lot_id")
        if not lot_id:
            return {
                "status": "complete",
                "answer": "Name a lot such as BLE-0457, FAR-118, or BIS-031.",
            }
        principal = _principal(state)
        require_tool(principal, "trace_lot")
        trace = store.trace(lot_id, "downstream")
        from datetime import date

        report = store.check_lot(lot_id, date.fromisoformat(as_of))
        certificates = list(trace.get("certificate_ids") or [])
        if certificates:
            note = f"{', '.join(certificates)} is still valid until 2027-12-31."
        else:
            note = "No valid certificate was found on the downstream lots."
        if not report.get("compliant"):
            codes = sorted({str(flag["code"]) for flag in report.get("flags") or []})
            note = "Compliance flags: " + ", ".join(codes) + ". " + note
        proposal = {
            "root_lot_id": lot_id,
            "downstream_lot_ids": list(trace["downstream_lot_ids"]),
            "retail_sites": list(trace["retail_sites"]),
            "shipment_ids": list(trace["shipment_ids"]),
            "certificate_note": note,
            "certificate_ids": certificates,
        }
        cites = citations_for_trace(trace)
        return {
            "trace": trace,
            "compliance": report,
            "recall_proposal": proposal,
            "citations": cites,
            "answer": render_recall_pending(proposal),
            "status": "needs_approval",
        }

    def approval_node(state: GraphState) -> dict[str, Any]:
        if state.get("status") == "complete":
            return {}
        decision = interrupt(
            {
                "type": "recall_approval",
                "question": "Approve this recall recommendation? Reply approve or reject.",
                "proposal": state.get("recall_proposal"),
            }
        )
        text = str(decision)
        principal = _principal(state)
        if text == "approve" and principal.role != "regulator":
            return {
                "human_decision": "reject",
                "approval_note": "Only a regulator can approve a recall.",
                "status": "running",
            }
        return {"human_decision": text, "approval_note": "", "status": "running"}

    def compose_node(state: GraphState) -> dict[str, Any]:
        if state.get("route") == "denied":
            return {}
        if state.get("status") == "complete" and not state.get("human_decision"):
            return {}
        route = state.get("route")
        citations: list[dict[str, str]]
        if route == "recall" and state.get("recall_proposal"):
            proposal = state["recall_proposal"] or {}
            answer = render_recall_final(
                proposal,
                str(state.get("human_decision") or "reject"),
                str(state.get("approval_note") or ""),
            )
            citations = list(state.get("citations") or [])
        elif route == "trace" and state.get("trace"):
            trace = state["trace"] or {}
            answer = render_trace(trace)
            citations = citations_for_trace(trace)
        elif route == "compliance" and state.get("compliance"):
            report = state["compliance"] or {}
            answer = render_compliance(report)
            citations = citations_for_compliance(report)
        elif route == "documents":
            hits = list(state.get("documents") or [])
            notes: list[str] = []
            principal = _principal(state)
            allowed = visible_lots(store.require_index(), principal)
            for hit in hits[:1]:
                for entity in hit.get("entity_ids") or []:
                    if str(entity).startswith(("BLE-", "FAR-", "BIS-", "OIL-")) and entity in allowed:
                        linked = store.trace(str(entity), "upstream")
                        notes.append(
                            f"Linked lot {entity} upstream: "
                            + ", ".join(str(item) for item in linked["upstream_lot_ids"])
                            + "."
                        )
                        break
            answer = render_documents(state.get("question") or "", hits, notes)
            citations = citations_for_documents(hits)
        else:
            answer = state.get("answer") or "No grounded result."
            citations = list(state.get("citations") or [])
        allowed_ids = set(ungrounded_ids(answer, set())) | {row["id"] for row in citations}
        if state.get("injection_flags"):
            narrative = (
                "Narrative suppressed: the question matched a prompt-injection pattern. "
                "Tool policy was not changed. Grounded result follows."
            )
            answer = narrative + "\n\n" + answer
        else:
            narrative = llm.narrate(state.get("question") or "", answer)
            if ungrounded_ids(narrative, allowed_ids):
                narrative = "Narrative suppressed: it introduced identifiers that were not retrieved."
            answer = answer + "\n\n" + narrative
        return {
            "answer": answer,
            "citations": citations,
            "status": "complete",
        }

    def choose(state: GraphState) -> str:
        return str(state.get("route") or "documents")

    builder: StateGraph[GraphState] = StateGraph(GraphState)
    builder.add_node("route", route_node)
    builder.add_node("trace", trace_node)
    builder.add_node("compliance", compliance_node)
    builder.add_node("documents", documents_node)
    builder.add_node("recall", recall_node)
    builder.add_node("approval", approval_node)
    builder.add_node("compose", compose_node)
    builder.set_entry_point("route")
    builder.add_conditional_edges(
        "route",
        choose,
        {
            "trace": "trace",
            "compliance": "compliance",
            "documents": "documents",
            "recall": "recall",
            "denied": END,
        },
    )
    builder.add_edge("trace", "compose")
    builder.add_edge("compliance", "compose")
    builder.add_edge("documents", "compose")
    builder.add_edge("recall", "approval")
    builder.add_edge("approval", "compose")
    builder.add_edge("compose", END)
    return builder.compile(checkpointer=MemorySaver())
