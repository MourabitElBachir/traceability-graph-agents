"""Domain records shared by the ERP extract, the graph, and the agents."""

from __future__ import annotations

from typing import Any, Literal

from pydantic import BaseModel, Field

ActorRole = Literal[
    "farm",
    "mill",
    "plant",
    "distributor",
    "retailer",
    "certifier",
    "auditor",
]
AccessRole = Literal[
    "producer",
    "processor",
    "distributor",
    "retailer",
    "certifier",
    "auditor",
    "regulator",
]
BizStep = Literal["commissioning", "transformation"]
CertStatus = Literal["valid", "expired", "suspended"]
AuditResult = Literal["conform", "minor", "major_nonconformity"]
DocKind = Literal["certificate", "audit", "procedure"]


class Actor(BaseModel):
    id: str
    name: str
    role: ActorRole


class Site(BaseModel):
    id: str
    name: str
    actor_id: str
    country: str
    gln: str


class Product(BaseModel):
    id: str
    name: str
    gtin: str
    category: str


class Ingredient(BaseModel):
    id: str
    name: str
    product_id: str
    parent_product_id: str


class LotQuantity(BaseModel):
    lot_id: str
    quantity: float
    unit: str = "kg"


class Lot(BaseModel):
    id: str
    lot_code: str
    product_id: str
    quantity: float
    unit: str
    produced_on: str
    site_id: str
    claimed_schemes: list[str] = Field(default_factory=list)


class ProcessStep(BaseModel):
    id: str
    biz_step: BizStep
    event_time: str
    site_id: str
    inputs: list[LotQuantity] = Field(default_factory=list)
    outputs: list[LotQuantity] = Field(default_factory=list)
    ingredient_ids: list[str] = Field(default_factory=list)


class Shipment(BaseModel):
    id: str
    shipped_on: str
    from_site_id: str
    to_site_id: str
    lot_ids: list[str]
    sscc: str


class Certificate(BaseModel):
    id: str
    scheme: str
    status: CertStatus
    valid_from: str
    valid_to: str
    issuer_actor_id: str
    holder_actor_id: str
    covers_lot_ids: list[str] = Field(default_factory=list)
    covers_site_ids: list[str] = Field(default_factory=list)
    covers_actor_ids: list[str] = Field(default_factory=list)


class Audit(BaseModel):
    id: str
    audit_date: str
    result: AuditResult
    site_id: str
    auditor_actor_id: str
    certificate_id: str | None
    summary: str


class Document(BaseModel):
    id: str
    title: str
    kind: DocKind
    text: str
    about_ids: list[str] = Field(default_factory=list)


class Dataset(BaseModel):
    """One consistent extract: the running example plus the anomaly cases."""

    actors: list[Actor]
    sites: list[Site]
    products: list[Product]
    ingredients: list[Ingredient]
    lots: list[Lot]
    processes: list[ProcessStep]
    shipments: list[Shipment]
    certificates: list[Certificate]
    audits: list[Audit]
    documents: list[Document]


class Citation(BaseModel):
    kind: Literal["node", "chunk"]
    id: str
    label: str
    detail: str


class AskResponse(BaseModel):
    status: Literal["complete", "needs_approval", "denied"]
    route: str
    answer: str
    citations: list[Citation]
    recall_proposal: dict[str, object] | None = None
    cypher: dict[str, object] | None = None
    principal: dict[str, Any]
    injection_flags: list[str] = Field(default_factory=list)
    audit_event_id: str
    thread_id: str
