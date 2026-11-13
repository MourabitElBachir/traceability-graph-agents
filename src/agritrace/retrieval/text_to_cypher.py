"""Schema-grounded text-to-Cypher. Mock mode never calls a model."""

from __future__ import annotations

from langchain_core.prompts import ChatPromptTemplate

from agritrace.graph.schema import schema_card
from agritrace.llm.provider import LLMClient
from agritrace.security.cypher_guard import CypherRejected, validate_cypher
from agritrace.security.guardrails import extract_lot_ids

CYPHER_PROMPT = ChatPromptTemplate.from_messages(
    [
        (
            "system",
            "Write one read-only Cypher query for the schema below. "
            "Use only the listed labels and relationships. "
            "Do not CREATE, MERGE, DELETE, SET, or CALL. "
            "End with LIMIT 25.\n{schema}",
        ),
        ("human", "{question}"),
    ]
)


def rule_based_cypher(question: str, as_of: str) -> tuple[str, dict[str, str]]:
    lot_ids = extract_lot_ids(question)
    lot_id = lot_ids[0] if lot_ids else ""
    lowered = question.lower()
    if "expired" in lowered or "périm" in lowered:
        cypher = (
            "MATCH (c:Certificate)\n"
            "WHERE c.status = 'expired' OR c.valid_to < date($as_of)\n"
            "RETURN c.id AS certificate_id, c.scheme AS scheme, c.valid_to AS valid_to\n"
            "LIMIT 25"
        )
        return cypher, {"as_of": as_of}
    if lot_id and any(word in lowered for word in ("upstream", "amont", "origin", "where")):
        cypher = (
            "MATCH (origin:Lot)-[:INPUT_OF*1..6]->(lot:Lot {id: $lot_id})\n"
            "RETURN origin.id AS origin_lot, lot.id AS lot_id\n"
            "LIMIT 25"
        )
        return cypher, {"lot_id": lot_id}
    if lot_id and any(word in lowered for word in ("certificate", "certificat", "cert-")):
        cypher = (
            "MATCH (c:Certificate)-[:COVERS]->(l:Lot {id: $lot_id})\n"
            "RETURN c.id AS certificate_id, c.scheme AS scheme, "
            "c.status AS status, c.valid_to AS valid_to\n"
            "LIMIT 25"
        )
        return cypher, {"lot_id": lot_id}
    if lot_id:
        cypher = (
            "MATCH (l:Lot {id: $lot_id})-[:OF_PRODUCT]->(p:Product)\nRETURN l.id AS lot_id, p.name AS product\nLIMIT 25"
        )
        return cypher, {"lot_id": lot_id}
    cypher = "MATCH (l:Lot)-[:OF_PRODUCT]->(p:Product)\nRETURN l.id AS lot_id, p.name AS product\nLIMIT 25"
    return cypher, {}


def draft_cypher(question: str, llm: LLMClient, as_of: str) -> dict[str, object]:
    """Validate before any execution. A rejected query is not retried into a write."""

    schema = schema_card()
    messages = CYPHER_PROMPT.format_messages(question=question, schema=schema)
    if llm.kind == "mock":
        cypher, params = rule_based_cypher(question, as_of)
    else:
        rendered = "\n".join(str(message.content) for message in messages)
        raw = llm.complete("Return only Cypher.", rendered)
        cypher, params = raw.strip(), {}
        lot_ids = extract_lot_ids(question)
        if lot_ids:
            params["lot_id"] = lot_ids[0]
        params.setdefault("as_of", as_of)
    try:
        safe = validate_cypher(cypher)
    except CypherRejected as exc:
        return {"ok": False, "error": str(exc), "cypher": cypher, "params": params}
    return {"ok": True, "cypher": safe, "params": params, "error": ""}
