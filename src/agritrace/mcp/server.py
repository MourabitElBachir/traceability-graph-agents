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


TOOLS = {
    "trace_lot": trace_lot,
    "check_certificates": check_certificates,
    "search_documents": search_documents,
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
