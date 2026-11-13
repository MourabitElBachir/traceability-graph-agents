"""Row-level visibility per actor.

Upstream of a lot you hold is visible (you may see where your product came from).
Downstream is visible for parties who must run a recall: producers, processors,
distributors, certifiers, auditors, and the regulator. A retailer does not see
other customers reached by a shared ancestor.
"""

from __future__ import annotations

from agritrace.graph.lineage import GraphIndex
from agritrace.models import AccessRole, Dataset

_DOWNSTREAM_ROLES = {"producer", "processor", "distributor", "certifier", "auditor", "regulator"}
_ROLE_BY_ACTOR = {
    "farm": "producer",
    "mill": "processor",
    "plant": "processor",
    "distributor": "distributor",
    "retailer": "retailer",
    "certifier": "certifier",
    "auditor": "auditor",
}
_TOOL_ROLES: dict[str, set[str]] = {
    "trace_lot": {
        "producer",
        "processor",
        "distributor",
        "retailer",
        "certifier",
        "auditor",
        "regulator",
    },
    "check_certificates": {
        "producer",
        "processor",
        "distributor",
        "retailer",
        "certifier",
        "auditor",
        "regulator",
    },
    "search_documents": {
        "producer",
        "processor",
        "distributor",
        "retailer",
        "certifier",
        "auditor",
        "regulator",
    },
    "read_cypher": {"auditor", "regulator"},
    "approve_recall": {"regulator"},
}


class Principal:
    def __init__(self, role: AccessRole, actor_id: str | None, name: str) -> None:
        self.role = role
        self.actor_id = actor_id
        self.name = name

    def as_dict(self) -> dict[str, str | None]:
        return {"role": self.role, "actor_id": self.actor_id, "name": self.name}


class AccessDenied(PermissionError):
    pass


def regulator() -> Principal:
    return Principal("regulator", None, "Demo regulator")


def principal_for_actor(dataset: Dataset, actor_id: str) -> Principal:
    actor = next(row for row in dataset.actors if row.id == actor_id)
    role = _ROLE_BY_ACTOR[actor.role]
    return Principal(role, actor.id, actor.name)  # type: ignore[arg-type]


def tool_allowed(role: str, tool: str) -> bool:
    return role in _TOOL_ROLES.get(tool, set())


def _sites_of(dataset: Dataset, actor_id: str) -> set[str]:
    return {site.id for site in dataset.sites if site.actor_id == actor_id}


def seed_lots(dataset: Dataset, principal: Principal) -> set[str]:
    if principal.role == "regulator" or principal.actor_id is None:
        return {lot.id for lot in dataset.lots}
    actor_id = principal.actor_id
    sites = _sites_of(dataset, actor_id)
    seeds: set[str] = set()
    if principal.role in {"producer", "processor"}:
        for lot in dataset.lots:
            if lot.site_id in sites:
                seeds.add(lot.id)
        for step in dataset.processes:
            if step.site_id in sites:
                for link in step.inputs + step.outputs:
                    seeds.add(link.lot_id)
    elif principal.role == "distributor":
        for shipment in dataset.shipments:
            if shipment.from_site_id in sites or shipment.to_site_id in sites:
                seeds.update(shipment.lot_ids)
    elif principal.role == "retailer":
        for shipment in dataset.shipments:
            if shipment.to_site_id in sites:
                seeds.update(shipment.lot_ids)
    elif principal.role == "certifier":
        for certificate in dataset.certificates:
            if certificate.issuer_actor_id == actor_id:
                seeds.update(certificate.covers_lot_ids)
    elif principal.role == "auditor":
        audited = {audit.site_id for audit in dataset.audits if audit.auditor_actor_id == actor_id}
        for lot in dataset.lots:
            if lot.site_id in audited:
                seeds.add(lot.id)
    return seeds


def visible_lots(index: GraphIndex, principal: Principal) -> set[str]:
    dataset = index.dataset
    if principal.role == "regulator":
        return {lot.id for lot in dataset.lots}
    seeds = seed_lots(dataset, principal)
    visible = set(seeds)
    expand_down = principal.role in _DOWNSTREAM_ROLES
    for lot_id in seeds:
        visible.update(index.walk(lot_id, downstream=False))
        if expand_down:
            visible.update(index.walk(lot_id, downstream=True))
    return visible


def require_lot(index: GraphIndex, principal: Principal, lot_id: str) -> None:
    if lot_id not in visible_lots(index, principal):
        raise AccessDenied(f"{principal.role} cannot access lot {lot_id}")


def require_tool(principal: Principal, tool: str) -> None:
    if not tool_allowed(principal.role, tool):
        raise AccessDenied(f"{principal.role} cannot call {tool}")
