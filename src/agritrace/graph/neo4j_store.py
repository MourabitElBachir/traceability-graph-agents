"""Persist the same extract to Neo4j: constraints, lineage edges, and a vector index.

Operational trace and compliance stay on the shared Python engine so CI and
Neo4j answer the same question. Guarded Cypher and the vector index run in Neo4j.
"""

from __future__ import annotations

from typing import Any

from agritrace.config import Settings
from agritrace.data.generator import ONTOLOGY_VERSION
from agritrace.graph.memory import MemoryStore
from agritrace.graph.schema import CONSTRAINTS, INDEXES, vector_index
from agritrace.security.cypher_guard import validate_cypher


class Neo4jStore:
    def __init__(self, settings: Settings, memory: MemoryStore) -> None:
        from neo4j import GraphDatabase

        self.settings = settings
        self.memory = memory
        self.driver = GraphDatabase.driver(
            settings.neo4j_uri,
            auth=(settings.neo4j_user, settings.neo4j_password),
        )

    def close(self) -> None:
        self.driver.close()

    def _run(self, cypher: str, **params: Any) -> list[dict[str, Any]]:
        with self.driver.session() as session:
            return session.run(cypher, **params).data()

    def ensure_schema(self) -> None:
        for statement in (*CONSTRAINTS, *INDEXES, vector_index(self.settings.embedding_dim)):
            self._run(statement)

    def sync(self) -> None:
        """Idempotent MERGE of the in-memory extract. Safe to call on every boot."""

        self.driver.verify_connectivity()
        self.ensure_schema()
        data = self.memory.require_index().dataset
        meta = {"source_system": "erp-sqlite", "ontology_version": ONTOLOGY_VERSION}
        for actor in data.actors:
            self._run(
                "MERGE (n:Actor {id: $id}) SET n.name = $name, n.role = $role, n += $meta",
                id=actor.id,
                name=actor.name,
                role=actor.role,
                meta=meta,
            )
        for site in data.sites:
            self._run(
                """
                MERGE (n:Site {id: $id})
                SET n.name = $name, n.country = $country, n.gln = $gln, n += $meta
                WITH n
                MATCH (a:Actor {id: $actor_id})
                MERGE (a)-[:OPERATES]->(n)
                """,
                id=site.id,
                name=site.name,
                country=site.country,
                gln=site.gln,
                actor_id=site.actor_id,
                meta=meta,
            )
        for product in data.products:
            self._run(
                "MERGE (n:Product {id: $id}) SET n.name = $name, n.gtin = $gtin, n.category = $category, n += $meta",
                id=product.id,
                name=product.name,
                gtin=product.gtin,
                category=product.category,
                meta=meta,
            )
        for lot in data.lots:
            self._run(
                """
                MERGE (n:Lot {id: $id})
                SET n.lot_code = $lot_code, n.quantity = $quantity, n.unit = $unit,
                    n.produced_on = $produced_on, n.claimed_schemes = $schemes, n += $meta
                WITH n
                MATCH (p:Product {id: $product_id})
                MERGE (n)-[:OF_PRODUCT]->(p)
                WITH n
                MATCH (s:Site {id: $site_id})
                MERGE (n)-[:PRODUCED_AT]->(s)
                """,
                id=lot.id,
                lot_code=lot.lot_code,
                quantity=lot.quantity,
                unit=lot.unit,
                produced_on=lot.produced_on,
                schemes=lot.claimed_schemes,
                product_id=lot.product_id,
                site_id=lot.site_id,
                meta=meta,
            )
        for step in data.processes:
            self._run(
                """
                MERGE (n:ProcessStep {id: $id})
                SET n.biz_step = $biz_step, n.event_time = $event_time, n += $meta
                WITH n
                MATCH (s:Site {id: $site_id})
                MERGE (n)-[:PERFORMED_AT]->(s)
                """,
                id=step.id,
                biz_step=step.biz_step,
                event_time=step.event_time,
                site_id=step.site_id,
                meta=meta,
            )
            for link in step.inputs:
                self._run(
                    """
                    MATCH (step:ProcessStep {id: $step_id})
                    MATCH (lot:Lot {id: $lot_id})
                    MERGE (step)-[r:CONSUMES]->(lot)
                    SET r.quantity = $quantity, r.unit = $unit
                    """,
                    step_id=step.id,
                    lot_id=link.lot_id,
                    quantity=link.quantity,
                    unit=link.unit,
                )
            for link in step.outputs:
                self._run(
                    """
                    MATCH (step:ProcessStep {id: $step_id})
                    MATCH (lot:Lot {id: $lot_id})
                    MERGE (step)-[r:PRODUCES]->(lot)
                    SET r.quantity = $quantity, r.unit = $unit
                    """,
                    step_id=step.id,
                    lot_id=link.lot_id,
                    quantity=link.quantity,
                    unit=link.unit,
                )
            for input_link in step.inputs:
                for output_link in step.outputs:
                    self._run(
                        """
                        MATCH (src:Lot {id: $src}), (dst:Lot {id: $dst})
                        MERGE (src)-[r:INPUT_OF]->(dst)
                        SET r.step_id = $step_id
                        """,
                        src=input_link.lot_id,
                        dst=output_link.lot_id,
                        step_id=step.id,
                    )
        for shipment in data.shipments:
            self._run(
                """
                MERGE (n:Shipment {id: $id})
                SET n.shipped_on = $shipped_on, n.sscc = $sscc, n += $meta
                WITH n
                MATCH (a:Site {id: $from_site}), (b:Site {id: $to_site})
                MERGE (n)-[:SHIPPED_FROM]->(a)
                MERGE (n)-[:SHIPPED_TO]->(b)
                """,
                id=shipment.id,
                shipped_on=shipment.shipped_on,
                sscc=shipment.sscc,
                from_site=shipment.from_site_id,
                to_site=shipment.to_site_id,
                meta=meta,
            )
            for lot_id in shipment.lot_ids:
                self._run(
                    "MATCH (n:Shipment {id: $id}), (l:Lot {id: $lot_id}) MERGE (n)-[:CONTAINS]->(l)",
                    id=shipment.id,
                    lot_id=lot_id,
                )
        for certificate in data.certificates:
            self._run(
                """
                MERGE (n:Certificate {id: $id})
                SET n.scheme = $scheme, n.status = $status, n.valid_from = $valid_from,
                    n.valid_to = $valid_to, n += $meta
                WITH n
                MATCH (issuer:Actor {id: $issuer}), (holder:Actor {id: $holder})
                MERGE (n)-[:ISSUED_BY]->(issuer)
                MERGE (n)-[:HELD_BY]->(holder)
                """,
                id=certificate.id,
                scheme=certificate.scheme,
                status=certificate.status,
                valid_from=certificate.valid_from,
                valid_to=certificate.valid_to,
                issuer=certificate.issuer_actor_id,
                holder=certificate.holder_actor_id,
                meta=meta,
            )
            for lot_id in certificate.covers_lot_ids:
                self._run(
                    "MATCH (c:Certificate {id: $id}), (l:Lot {id: $lot_id}) MERGE (c)-[:COVERS]->(l)",
                    id=certificate.id,
                    lot_id=lot_id,
                )
            for site_id in certificate.covers_site_ids:
                self._run(
                    "MATCH (c:Certificate {id: $id}), (s:Site {id: $site_id}) MERGE (c)-[:COVERS]->(s)",
                    id=certificate.id,
                    site_id=site_id,
                )
            for actor_id in certificate.covers_actor_ids:
                self._run(
                    "MATCH (c:Certificate {id: $id}), (a:Actor {id: $actor_id}) MERGE (c)-[:COVERS]->(a)",
                    id=certificate.id,
                    actor_id=actor_id,
                )
        for audit in data.audits:
            self._run(
                """
                MERGE (n:Audit {id: $id})
                SET n.audit_date = $audit_date, n.result = $result, n.summary = $summary, n += $meta
                WITH n
                MATCH (s:Site {id: $site_id})
                MERGE (n)-[:AUDITS]->(s)
                """,
                id=audit.id,
                audit_date=audit.audit_date,
                result=audit.result,
                summary=audit.summary,
                site_id=audit.site_id,
                meta=meta,
            )
            if audit.certificate_id:
                self._run(
                    """
                    MATCH (n:Audit {id: $id}), (c:Certificate {id: $certificate_id})
                    MERGE (n)-[:EVIDENCES]->(c)
                    """,
                    id=audit.id,
                    certificate_id=audit.certificate_id,
                )
        for document in data.documents:
            self._run(
                "MERGE (n:Document {id: $id}) SET n.title = $title, n.kind = $kind, n += $meta",
                id=document.id,
                title=document.title,
                kind=document.kind,
                meta=meta,
            )
        for chunk in self.memory.chunks:
            self._run(
                """
                MERGE (c:Chunk {id: $id})
                SET c.text = $text, c.embedding = $embedding, c.document_id = $document_id, c += $meta
                WITH c
                MATCH (d:Document {id: $document_id})
                MERGE (c)-[:PART_OF]->(d)
                """,
                id=chunk.id,
                text=chunk.text,
                embedding=chunk.embedding,
                document_id=chunk.document_id,
                meta=meta,
            )
            for entity_id in chunk.entity_ids:
                self._run(
                    """
                    MATCH (c:Chunk {id: $chunk_id})
                    OPTIONAL MATCH (n {id: $entity_id})
                    WITH c, n WHERE n IS NOT NULL
                    MERGE (c)-[:MENTIONS]->(n)
                    """,
                    chunk_id=chunk.id,
                    entity_id=entity_id,
                )

    def run_read_cypher(self, cypher: str, params: dict[str, str]) -> list[dict[str, Any]]:
        safe = validate_cypher(cypher)
        return self._run(safe, **params)
