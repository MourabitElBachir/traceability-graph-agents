"""Keyword router. Mock mode does not ask a model to choose a tool."""

from __future__ import annotations

from dataclasses import dataclass

from agritrace.security.guardrails import extract_certificate_ids, extract_lot_ids


@dataclass(frozen=True)
class RouteDecision:
    route: str
    lot_id: str | None
    direction: str
    certificate_id: str | None


def route_question(question: str) -> RouteDecision:
    lot_ids = extract_lot_ids(question)
    certificate_ids = extract_certificate_ids(question)
    lot_id = lot_ids[0] if lot_ids else None
    certificate_id = certificate_ids[0] if certificate_ids else None
    lowered = question.lower()
    if any(word in lowered for word in ("upstream", "amont")):
        direction = "upstream"
    elif any(word in lowered for word in ("downstream", "aval")):
        direction = "downstream"
    else:
        direction = "both"
    if any(word in lowered for word in ("recall", "retrait", "rappel", "withdraw")):
        return RouteDecision("recall", lot_id, "downstream", certificate_id)
    if "chain complete" in lowered or "broken chain" in lowered or "chaîne" in lowered:
        return RouteDecision("compliance", lot_id, "upstream", certificate_id)
    documentish = any(word in lowered for word in ("audit", "document", "report", "rapport", "playbook"))
    complianceish = any(
        word in lowered for word in ("certificate", "certificat", "compliant", "conform", "expired", "périm", "organic")
    )
    if documentish and not complianceish:
        return RouteDecision("documents", lot_id, direction, certificate_id)
    if certificate_id or complianceish:
        return RouteDecision("compliance", lot_id, "upstream", certificate_id)
    if lot_id or any(word in lowered for word in ("trace", "traç", "where", "où")):
        return RouteDecision("trace", lot_id, direction, certificate_id)
    return RouteDecision("documents", None, "both", certificate_id)
