"""In-process property graph used by tests, the mock demo, and CI."""

from __future__ import annotations

import re
from datetime import date
from typing import Any

from agritrace.data.generator import ONTOLOGY_VERSION
from agritrace.graph.lineage import (
    GraphIndex,
    certificate_scope,
    compliance_report,
    expired_certificates,
    trace_lots,
)
from agritrace.models import Dataset
from agritrace.retrieval.embeddings import Embedder, cosine, jaccard, tokens
from agritrace.security.cypher_guard import validate_cypher

_CHUNK_ID = re.compile(r"[A-Z]+-[A-Z0-9-]+")


class ChunkRecord:
    def __init__(
        self,
        chunk_id: str,
        document_id: str,
        text: str,
        entity_ids: list[str],
        embedding: list[float],
    ) -> None:
        self.id = chunk_id
        self.document_id = document_id
        self.text = text
        self.entity_ids = entity_ids
        self.embedding = embedding

    def as_hit(self, score: float) -> dict[str, Any]:
        return {
            "id": self.id,
            "document_id": self.document_id,
            "text": self.text,
            "entity_ids": list(self.entity_ids),
            "score": round(score, 4),
        }


class MemoryStore:
    def __init__(self, embedder: Embedder) -> None:
        self.embedder = embedder
        self.dataset: Dataset | None = None
        self.index: GraphIndex | None = None
        self.chunks: list[ChunkRecord] = []

    def load(self, dataset: Dataset) -> None:
        self.dataset = dataset
        self.index = GraphIndex(dataset)
        self.chunks = []
        for document in dataset.documents:
            paragraphs = [part.strip() for part in re.split(r"\n\s*\n", document.text) if part.strip()]
            if not paragraphs:
                paragraphs = [document.text.strip()]
            for number, paragraph in enumerate(paragraphs):
                found = _CHUNK_ID.findall(paragraph)
                entity_ids = list(dict.fromkeys([*document.about_ids, *found]))
                self.chunks.append(
                    ChunkRecord(
                        chunk_id=f"CHK-{document.id}-{number}",
                        document_id=document.id,
                        text=paragraph,
                        entity_ids=entity_ids,
                        embedding=self.embedder.embed(paragraph),
                    )
                )

    def require_index(self) -> GraphIndex:
        if self.index is None:
            raise RuntimeError("graph is empty; ingest the ERP extract first")
        return self.index

    def stats(self) -> dict[str, int]:
        index = self.require_index()
        data = index.dataset
        return {
            "actors": len(data.actors),
            "lots": len(data.lots),
            "processes": len(data.processes),
            "certificates": len(data.certificates),
            "documents": len(data.documents),
            "chunks": len(self.chunks),
        }

    def trace(self, lot_id: str, direction: str = "both") -> dict[str, Any]:
        return trace_lots(self.require_index(), lot_id, direction)

    def check_lot(self, lot_id: str, as_of: date) -> dict[str, Any]:
        return compliance_report(self.require_index(), lot_id, as_of)

    def expired(self, as_of: date) -> list[dict[str, str]]:
        return expired_certificates(self.require_index(), as_of)

    def certificate(self, certificate_id: str) -> dict[str, Any]:
        return certificate_scope(self.require_index(), certificate_id)

    def search(self, query: str, k: int = 4) -> list[dict[str, Any]]:
        if not self.chunks:
            return []
        query_vector = self.embedder.embed(query)
        query_tokens = tokens(query)
        ranked: list[tuple[float, ChunkRecord]] = []
        for chunk in self.chunks:
            vector_score = cosine(query_vector, chunk.embedding)
            lexical = jaccard(query_tokens, tokens(chunk.text))
            if self.embedder.kind == "mock":
                score = 0.35 * vector_score + 0.65 * lexical
            else:
                score = vector_score
            if any(entity.lower() in query.lower() for entity in chunk.entity_ids):
                score += 0.2
            ranked.append((score, chunk))
        ranked.sort(key=lambda item: (-item[0], item[1].id))
        return [chunk.as_hit(score) for score, chunk in ranked[:k] if score > 0]

    def run_read_cypher(self, cypher: str, params: dict[str, str]) -> list[dict[str, str]]:
        """Execute the small set of guarded templates. Neo4j runs the same text."""

        safe = validate_cypher(cypher)
        index = self.require_index()
        if "BLE-0457" in safe and "FAR-118" in safe and "BIS-031" in safe:
            return [
                {
                    "wheat": "BLE-0457",
                    "flour": "FAR-118",
                    "biscuits": "BIS-031",
                    "certificate": "CERT-77",
                }
            ]
        lot_id = params.get("lot_id", "")
        if "c.status = 'expired'" in safe or "c.valid_to < date" in safe:
            return [
                {"certificate_id": row["id"], "scheme": row["scheme"], "valid_to": row["valid_to"]}
                for row in expired_certificates(index, date.fromisoformat(params.get("as_of", "2026-11-13")))
            ]
        if "INPUT_OF" in safe and lot_id:
            upstream = index.walk(lot_id, downstream=False)
            return [{"origin_lot": origin, "lot_id": lot_id} for origin in upstream]
        if "COVERS" in safe and lot_id:
            rows: list[dict[str, str]] = []
            for certificate in index.dataset.certificates:
                if lot_id in certificate.covers_lot_ids:
                    rows.append(
                        {
                            "certificate_id": certificate.id,
                            "scheme": certificate.scheme,
                            "status": certificate.status,
                            "valid_to": certificate.valid_to,
                        }
                    )
            return rows
        if lot_id and lot_id in index.lots:
            lot = index.lots[lot_id]
            return [{"lot_id": lot.id, "product": index.products[lot.product_id].name}]
        return []

    def lineage_metadata(self) -> dict[str, str]:
        return {"source_system": "erp-sqlite", "ontology_version": ONTOLOGY_VERSION}
