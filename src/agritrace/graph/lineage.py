"""Lot lineage and certificate checks shared by every graph backend."""

from __future__ import annotations

from collections import defaultdict, deque
from datetime import date
from typing import Any

from agritrace.models import Certificate, Dataset, Lot, ProcessStep


def _as_date(value: str) -> date:
    return date.fromisoformat(value[:10])


class GraphIndex:
    """Adjacency built once from a dataset."""

    def __init__(self, dataset: Dataset) -> None:
        self.dataset = dataset
        self.lots = {row.id: row for row in dataset.lots}
        self.sites = {row.id: row for row in dataset.sites}
        self.actors = {row.id: row for row in dataset.actors}
        self.products = {row.id: row for row in dataset.products}
        self.certificates = {row.id: row for row in dataset.certificates}
        self.by_output: dict[str, list[ProcessStep]] = defaultdict(list)
        self.by_input: dict[str, list[ProcessStep]] = defaultdict(list)
        for step in dataset.processes:
            for link in step.outputs:
                self.by_output[link.lot_id].append(step)
            for link in step.inputs:
                self.by_input[link.lot_id].append(step)

    def walk(self, start: str, downstream: bool) -> list[str]:
        found: list[str] = []
        seen = {start}
        queue: deque[str] = deque([start])
        while queue:
            current = queue.popleft()
            steps = self.by_input[current] if downstream else self.by_output[current]
            for step in steps:
                links = step.outputs if downstream else step.inputs
                for link in links:
                    if link.lot_id not in seen:
                        seen.add(link.lot_id)
                        found.append(link.lot_id)
                        queue.append(link.lot_id)
        return found

    def steps_between(self, lot_ids: set[str]) -> list[str]:
        step_ids: list[str] = []
        for step in self.dataset.processes:
            touched = {link.lot_id for link in step.inputs + step.outputs}
            if touched & lot_ids:
                step_ids.append(step.id)
        return step_ids


def _cert_valid(certificate: Certificate, as_of: date) -> bool:
    return certificate.status == "valid" and _as_date(certificate.valid_from) <= as_of <= _as_date(certificate.valid_to)


def _covering(index: GraphIndex, lot: Lot, scheme: str) -> list[Certificate]:
    return [
        certificate
        for certificate in index.dataset.certificates
        if certificate.scheme == scheme and lot.id in certificate.covers_lot_ids
    ]


def coverage_label(index: GraphIndex, lot_id: str, as_of: date) -> str:
    lot = index.lots[lot_id]
    if not lot.claimed_schemes:
        return "unclaimed"
    labels: list[str] = []
    for scheme in lot.claimed_schemes:
        covering = _covering(index, lot, scheme)
        if any(_cert_valid(certificate, as_of) for certificate in covering):
            labels.append(f"valid:{scheme}")
        elif any(certificate.status == "expired" or _as_date(certificate.valid_to) < as_of for certificate in covering):
            labels.append(f"expired:{scheme}")
        else:
            labels.append(f"none:{scheme}")
    return "|".join(labels)


def compliance_report(index: GraphIndex, lot_id: str, as_of: date) -> dict[str, Any]:
    if lot_id not in index.lots:
        raise KeyError(lot_id)
    walked = [lot_id, *index.walk(lot_id, downstream=False)]
    flags: list[dict[str, str]] = []
    certificate_ids: list[str] = []
    for current_id in walked:
        lot = index.lots[current_id]
        for scheme in lot.claimed_schemes:
            covering = _covering(index, lot, scheme)
            for certificate in covering:
                if certificate.id not in certificate_ids:
                    certificate_ids.append(certificate.id)
                if certificate.status == "expired" or _as_date(certificate.valid_to) < as_of:
                    flags.append(
                        {
                            "code": "expired_certificate",
                            "lot_id": current_id,
                            "certificate_id": certificate.id,
                            "step_id": "",
                            "detail": (
                                f"{certificate.id} ({certificate.scheme}) valid_to "
                                f"{certificate.valid_to} is expired for {current_id}"
                            ),
                        }
                    )
            if not any(_cert_valid(certificate, as_of) for certificate in covering):
                flags.append(
                    {
                        "code": "claim_without_valid_certificate",
                        "lot_id": current_id,
                        "certificate_id": "",
                        "step_id": "",
                        "detail": f"{current_id} claims {scheme} without a valid covering certificate",
                    }
                )
        for step in index.by_output[current_id]:
            if step.biz_step == "transformation" and not step.inputs:
                site = index.sites[step.site_id]
                flags.append(
                    {
                        "code": "broken_chain",
                        "lot_id": current_id,
                        "certificate_id": "",
                        "step_id": step.id,
                        "detail": (f"transformation {step.id} at {site.name} ({site.id}) has no source lot"),
                    }
                )
            if step.biz_step == "transformation" and len(step.inputs) >= 2:
                labels = {coverage_label(index, link.lot_id, as_of) for link in step.inputs}
                if len(labels) > 1:
                    joined = ", ".join(link.lot_id for link in step.inputs)
                    flags.append(
                        {
                            "code": "mixed_lots",
                            "lot_id": current_id,
                            "certificate_id": "",
                            "step_id": step.id,
                            "detail": f"{step.id} mixes {joined} with states {sorted(labels)}",
                        }
                    )
        if not index.by_output[current_id]:
            flags.append(
                {
                    "code": "broken_chain",
                    "lot_id": current_id,
                    "certificate_id": "",
                    "step_id": "",
                    "detail": f"{current_id} has no commissioning or transformation event",
                }
            )
    deduped: list[dict[str, str]] = []
    seen_flags: set[tuple[str, str, str, str]] = set()
    for flag in flags:
        key = (flag["code"], flag["lot_id"], flag["certificate_id"], flag["step_id"])
        if key not in seen_flags:
            seen_flags.add(key)
            deduped.append(flag)
    focal = index.lots[lot_id]
    summaries = [
        (f"{certificate.id} ({certificate.scheme}, status {certificate.status}, valid_to {certificate.valid_to})")
        for certificate_id in certificate_ids
        for certificate in [index.certificates[certificate_id]]
    ]
    return {
        "lot_id": lot_id,
        "as_of": as_of.isoformat(),
        "compliant": not deduped,
        "schemes": list(focal.claimed_schemes),
        "product_name": index.products[focal.product_id].name,
        "site_name": index.sites[focal.site_id].name,
        "site_id": focal.site_id,
        "upstream_lot_ids": [item for item in walked if item != lot_id],
        "certificate_ids": certificate_ids,
        "certificate_summaries": summaries,
        "flags": deduped,
    }


def expired_certificates(index: GraphIndex, as_of: date) -> list[dict[str, str]]:
    rows: list[dict[str, str]] = []
    for certificate in index.dataset.certificates:
        if certificate.status == "expired" or _as_date(certificate.valid_to) < as_of:
            holder = index.actors[certificate.holder_actor_id]
            rows.append(
                {
                    "id": certificate.id,
                    "scheme": certificate.scheme,
                    "status": "expired",
                    "valid_to": certificate.valid_to,
                    "holder": holder.name,
                    "holder_actor_id": holder.id,
                }
            )
    return rows


def certificate_scope(index: GraphIndex, certificate_id: str) -> dict[str, Any]:
    certificate = index.certificates[certificate_id]
    holder = index.actors[certificate.holder_actor_id]
    return {
        "id": certificate.id,
        "scheme": certificate.scheme,
        "status": certificate.status,
        "valid_from": certificate.valid_from,
        "valid_to": certificate.valid_to,
        "holder": holder.name,
        "holder_actor_id": holder.id,
        "covers_lot_ids": list(certificate.covers_lot_ids),
        "covers_site_ids": list(certificate.covers_site_ids),
    }


def trace_lots(index: GraphIndex, lot_id: str, direction: str) -> dict[str, Any]:
    if lot_id not in index.lots:
        raise KeyError(lot_id)
    upstream = index.walk(lot_id, downstream=False) if direction in {"upstream", "both"} else []
    downstream = index.walk(lot_id, downstream=True) if direction in {"downstream", "both"} else []
    if direction == "upstream":
        ordered = [*reversed(upstream), lot_id]
    elif direction == "downstream":
        ordered = [lot_id, *downstream]
    else:
        ordered = [*reversed(upstream), lot_id, *downstream]
    path_ids = set(ordered)
    shipments = [row for row in index.dataset.shipments if path_ids & set(row.lot_ids)]
    site_ids: list[str] = []
    for current in ordered:
        site_id = index.lots[current].site_id
        if site_id not in site_ids:
            site_ids.append(site_id)
    for shipment in shipments:
        for site_id in (shipment.from_site_id, shipment.to_site_id):
            if site_id not in site_ids:
                site_ids.append(site_id)
    actor_ids: list[str] = []
    retail_sites: list[str] = []
    for site_id in site_ids:
        site = index.sites[site_id]
        if site.actor_id not in actor_ids:
            actor_ids.append(site.actor_id)
        if site.actor_id and index.actors[site.actor_id].role == "retailer":
            retail_sites.append(f"{site.name} ({site.id})")
    certificate_ids: list[str] = []
    for certificate in index.dataset.certificates:
        if path_ids & set(certificate.covers_lot_ids):
            certificate_ids.append(certificate.id)
    origin = index.lots[ordered[0]]
    origin_site = index.sites[origin.site_id]
    origin_actor = index.actors[origin_site.actor_id]
    focal = index.lots[lot_id]
    return {
        "root_lot_id": lot_id,
        "direction": direction,
        "product_name": index.products[focal.product_id].name,
        "lot_ids": ordered,
        "path_lot_ids": ordered,
        "upstream_lot_ids": upstream,
        "downstream_lot_ids": downstream,
        "process_ids": index.steps_between(path_ids),
        "shipment_ids": [row.id for row in shipments],
        "site_ids": site_ids,
        "actor_ids": actor_ids,
        "certificate_ids": certificate_ids,
        "origin_lot_id": origin.id,
        "origin_site_id": origin_site.id,
        "origin_site_name": origin_site.name,
        "origin_actor_id": origin_actor.id,
        "origin_actor_name": origin_actor.name,
        "retail_sites": retail_sites,
    }
