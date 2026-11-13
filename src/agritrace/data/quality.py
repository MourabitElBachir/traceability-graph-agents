"""Structural data-quality checks. Business anomalies are findings, not load errors."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import date

from agritrace.models import Dataset


@dataclass
class QualityReport:
    errors: list[str] = field(default_factory=list)
    findings: list[str] = field(default_factory=list)

    @property
    def ok(self) -> bool:
        return not self.errors


def _parse(value: str) -> date:
    return date.fromisoformat(value[:10])


def check_quality(dataset: Dataset) -> QualityReport:
    """Referential integrity and a few agrifood invariants.

    Expired certificates, mixed lots, and a transformation with no source lot
    are recorded as findings. They are the point of the demo and must load.
    """

    report = QualityReport()
    actors = {row.id for row in dataset.actors}
    sites = {row.id: row for row in dataset.sites}
    products = {row.id for row in dataset.products}
    ingredients = {row.id for row in dataset.ingredients}
    lots = {row.id: row for row in dataset.lots}
    certificates = {row.id for row in dataset.certificates}

    def need(kind: str, ident: str, pool: set[str]) -> None:
        if ident not in pool:
            report.errors.append(f"unknown {kind} {ident}")

    for site in dataset.sites:
        need("actor", site.actor_id, actors)
    for ingredient in dataset.ingredients:
        need("product", ingredient.product_id, products)
        need("product", ingredient.parent_product_id, products)
    for lot in dataset.lots:
        need("product", lot.product_id, products)
        if lot.site_id not in sites:
            report.errors.append(f"lot {lot.id} has unknown site {lot.site_id}")
        if lot.quantity <= 0:
            report.errors.append(f"lot {lot.id} has a non-positive quantity")
    seen: set[str] = set()
    for collection in (
        dataset.actors,
        dataset.sites,
        dataset.products,
        dataset.lots,
        dataset.processes,
        dataset.shipments,
        dataset.certificates,
        dataset.audits,
        dataset.documents,
    ):
        for row in collection:
            if row.id in seen:
                report.errors.append(f"duplicate id {row.id}")
            seen.add(row.id)

    for step in dataset.processes:
        if step.site_id not in sites:
            report.errors.append(f"process {step.id} has unknown site {step.site_id}")
        for link in step.inputs + step.outputs:
            if link.lot_id not in lots:
                report.errors.append(f"process {step.id} references unknown lot {link.lot_id}")
        for ingredient_id in step.ingredient_ids:
            if ingredient_id not in ingredients:
                report.errors.append(f"process {step.id} uses unknown ingredient {ingredient_id}")
        if step.biz_step == "transformation" and not step.inputs:
            report.findings.append(f"broken_chain:{step.id}")
        if step.biz_step == "commissioning" and step.inputs:
            report.errors.append(f"commissioning {step.id} should not consume lots")
        if not step.outputs:
            report.errors.append(f"process {step.id} produces nothing")

    for shipment in dataset.shipments:
        if shipment.from_site_id not in sites or shipment.to_site_id not in sites:
            report.errors.append(f"shipment {shipment.id} references an unknown site")
        for lot_id in shipment.lot_ids:
            if lot_id not in lots:
                report.errors.append(f"shipment {shipment.id} contains unknown lot {lot_id}")

    for certificate in dataset.certificates:
        need("actor", certificate.issuer_actor_id, actors)
        need("actor", certificate.holder_actor_id, actors)
        if _parse(certificate.valid_from) > _parse(certificate.valid_to):
            report.errors.append(f"certificate {certificate.id} has inverted validity dates")
        for lot_id in certificate.covers_lot_ids:
            if lot_id not in lots:
                report.errors.append(f"certificate {certificate.id} covers unknown lot {lot_id}")
        if certificate.status == "expired":
            report.findings.append(f"expired_certificate:{certificate.id}")

    for audit in dataset.audits:
        if audit.site_id not in sites:
            report.errors.append(f"audit {audit.id} references unknown site {audit.site_id}")
        need("actor", audit.auditor_actor_id, actors)
        if audit.certificate_id and audit.certificate_id not in certificates:
            report.errors.append(f"audit {audit.id} evidences unknown certificate")

    known = seen | ingredients
    for document in dataset.documents:
        for ident in document.about_ids:
            if ident not in known:
                report.errors.append(f"document {document.id} is about unknown id {ident}")
        if not document.text.strip():
            report.errors.append(f"document {document.id} is empty")
    return report
