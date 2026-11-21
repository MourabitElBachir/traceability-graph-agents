"""MCP server. Tools call the same service as the API. Default actor is the demo regulator."""

from __future__ import annotations

import json
from collections.abc import Callable
from typing import Any, cast

from agritrace.security.rbac import AccessDenied
from agritrace.service import TraceService, build_service

_SERVICE: TraceService | None = None


def get_service() -> TraceService:
    global _SERVICE
    if _SERVICE is None:
        _SERVICE = build_service()
    return _SERVICE


def _caller(service: TraceService, actor_id: str) -> Any:
    return service.principal_from_actor(actor_id or None)


def trace_lot(lot_id: str, direction: str = "both", actor_id: str = "") -> str:
    """Trace a lot upstream, downstream, or both. Example lot ids: BLE-0457, FAR-118, BIS-031."""

    service = get_service()
    try:
        payload = service.trace(lot_id, direction, _caller(service, actor_id))
    except AccessDenied as exc:
        payload = {"error": str(exc), "lot_id": lot_id}
    except KeyError:
        payload = {"error": f"unknown lot {lot_id}"}
    return json.dumps(payload, ensure_ascii=False)


def check_certificates(lot_id: str, actor_id: str = "") -> str:
    """Check certificate validity for a lot as of the demo clock. CERT-77 covers BIS-031."""

    service = get_service()
    try:
        payload = service.check(lot_id, _caller(service, actor_id))
    except AccessDenied as exc:
        payload = {"error": str(exc), "lot_id": lot_id}
    except KeyError:
        payload = {"error": f"unknown lot {lot_id}"}
    return json.dumps(payload, ensure_ascii=False)


def search_documents(query: str, k: int = 4, actor_id: str = "") -> str:
    """Search certificate and audit text visible to the caller."""

    service = get_service()
    payload: Any
    try:
        payload = service.search(query, k, _caller(service, actor_id))
    except AccessDenied as exc:
        payload = {"error": str(exc)}
    return json.dumps(payload, ensure_ascii=False)


def optimize_recall_plan(lot_id: str, scenario: str = "baseline", actor_id: str = "") -> str:
    """Choose block, quarantine, redirect, or recall for lots downstream of lot_id.

    A plan is a recommendation. It does not issue a recall. scenario is baseline,
    no_lab_capacity, or biscuits_not_delivered.
    """

    from agritrace.optimization.solve import compare_plans

    service = get_service()
    scenarios: dict[str, dict[str, Any]] = {
        "baseline": {},
        "no_lab_capacity": {"lab_tests_per_day": 0},
        "biscuits_not_delivered": {"delivered": {"BIS-031": False}},
    }
    if scenario not in scenarios:
        return json.dumps({"error": f"unknown scenario {scenario}"})
    try:
        caller = _caller(service, actor_id)
        from agritrace.security.rbac import require_lot, require_tool

        require_tool(caller, "optimize_recall_plan")
        require_lot(service.store.require_index(), caller, lot_id)
        plans = compare_plans(
            service.store,
            lot_id,
            service.settings.as_of,
            [(scenario, scenarios[scenario])],
        )
        payload: Any = plans[0]
        service.audit.record(
            action="optimize_recall_plan",
            allowed=True,
            principal_role=caller.role,
            principal_actor_id=caller.actor_id,
            lot_id=lot_id,
            detail=scenario,
        )
    except AccessDenied as exc:
        payload = {"error": str(exc), "lot_id": lot_id}
    except KeyError:
        payload = {"error": f"unknown lot {lot_id}"}
    return json.dumps(payload, ensure_ascii=False)


TOOLS = {
    "trace_lot": trace_lot,
    "check_certificates": check_certificates,
    "search_documents": search_documents,
    "optimize_recall_plan": optimize_recall_plan,
}


def build_mcp() -> Any:
    from mcp.server.mcpserver import MCPServer

    server = MCPServer(
        "agritrace",
        instructions=(
            "Fictional agrifood traceability tools. "
            "The running example is wheat BLE-0457, flour FAR-118, biscuits BIS-031, certificate CERT-77."
        ),
    )
    for fn in TOOLS.values():
        server.add_tool(cast(Callable[..., Any], fn))
    return server


def main() -> None:
    build_mcp().run(transport="stdio")
