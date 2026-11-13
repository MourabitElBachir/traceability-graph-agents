"""Neo4j constraints and the allow-lists shared with the Cypher guard."""

from __future__ import annotations

LABELS: tuple[str, ...] = (
    "Actor",
    "Site",
    "Product",
    "Ingredient",
    "Lot",
    "ProcessStep",
    "Shipment",
    "Certificate",
    "Audit",
    "Document",
    "Chunk",
)

RELATIONSHIPS: tuple[str, ...] = (
    "OPERATES",
    "PRODUCED_AT",
    "OF_PRODUCT",
    "CONSUMES",
    "PRODUCES",
    "PERFORMED_AT",
    "INPUT_OF",
    "CONTAINS",
    "SHIPPED_FROM",
    "SHIPPED_TO",
    "COVERS",
    "ISSUED_BY",
    "HELD_BY",
    "AUDITS",
    "EVIDENCES",
    "ABOUT",
    "PART_OF",
    "MENTIONS",
    "INGREDIENT_OF",
    "USED_IN",
)

CONSTRAINTS: tuple[str, ...] = tuple(
    f"CREATE CONSTRAINT {label.lower()}_id IF NOT EXISTS FOR (n:{label}) REQUIRE n.id IS UNIQUE" for label in LABELS
)

INDEXES: tuple[str, ...] = (
    "CREATE INDEX lot_code IF NOT EXISTS FOR (n:Lot) ON (n.lot_code)",
    "CREATE INDEX certificate_valid_to IF NOT EXISTS FOR (n:Certificate) ON (n.valid_to)",
    "CREATE INDEX process_biz_step IF NOT EXISTS FOR (n:ProcessStep) ON (n.biz_step)",
)


def vector_index(dimensions: int) -> str:
    return (
        "CREATE VECTOR INDEX chunk_embedding IF NOT EXISTS "
        "FOR (c:Chunk) ON (c.embedding) "
        "OPTIONS {indexConfig: { "
        f"`vector.dimensions`: {int(dimensions)}, "
        "`vector.similarity_function`: 'cosine' }}"
    )


def schema_card() -> str:
    labels = ", ".join(LABELS)
    rels = ", ".join(RELATIONSHIPS)
    return (
        "Read-only property graph.\n"
        f"Node labels: {labels}.\n"
        f"Relationship types: {rels}.\n"
        "Lot.id values include BLE-0457, FAR-118, BIS-031.\n"
        "Certificate.id CERT-77 covers those three lots.\n"
        "Derived lineage is (input:Lot)-[:INPUT_OF]->(output:Lot).\n"
        "Return only a single MATCH query with an explicit LIMIT."
    )
