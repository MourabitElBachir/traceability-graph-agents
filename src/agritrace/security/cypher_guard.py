"""Reject anything that is not a single read-only, schema-grounded Cypher query."""

from __future__ import annotations

import re

from agritrace.graph.schema import LABELS, RELATIONSHIPS

_WRITE = re.compile(
    r"\b(CREATE|MERGE|DELETE|DETACH|SET|REMOVE|DROP|LOAD|FOREACH|CALL|INSERT|UPDATE|GRANT|"
    r"REVOKE|ALTER|SHOW|TERMINATE)\b",
    re.IGNORECASE,
)
_COMMENT = re.compile(r"//|/\*|\*/")
_FUNC = re.compile(r"\b([A-Za-z_][A-Za-z0-9_]*)\s*\(")
_REL = re.compile(r"\[\s*(?:\w+\s*)?:([A-Za-z_][A-Za-z0-9_]*)")
_LABEL = re.compile(r":([A-Za-z_][A-Za-z0-9_]*)")
_LIMIT = re.compile(r"\bLIMIT\s+(\d+)\b", re.IGNORECASE)
_ALLOWED_FUNCS = {"date", "count", "tolower", "coalesce", "tostring"}
_NOT_FUNCS = {
    "match",
    "optional",
    "where",
    "return",
    "with",
    "order",
    "and",
    "or",
    "as",
    "not",
    "in",
    "distinct",
    "by",
    "asc",
    "desc",
    "limit",
    "skip",
    "case",
    "when",
    "then",
    "else",
    "end",
    "xor",
    "true",
    "false",
    "null",
}
_CAP = 50


class CypherRejected(ValueError):
    """The query failed a guardrail and must not be executed."""


def validate_cypher(cypher: str, cap: int = _CAP) -> str:
    """Return the query with a bounded LIMIT, or raise CypherRejected."""

    text = cypher.strip()
    if not text:
        raise CypherRejected("empty query")
    if _COMMENT.search(text) or ";" in text:
        raise CypherRejected("comments and multiple statements are rejected")
    if _WRITE.search(text):
        raise CypherRejected("only a read-only MATCH query is allowed")
    if not re.match(r"(?is)\s*MATCH\b", text):
        raise CypherRejected("query must start with MATCH")
    if not re.search(r"(?i)\bRETURN\b", text):
        raise CypherRejected("query must RETURN rows")

    for name in _FUNC.findall(text):
        lowered = name.lower()
        if lowered in _NOT_FUNCS:
            continue
        if lowered not in _ALLOWED_FUNCS:
            raise CypherRejected(f"function {name} is not allowed")

    rel_types = set(_REL.findall(text))
    without_rels = _REL.sub("", text)
    labels = set(_LABEL.findall(without_rels))
    unknown_labels = labels - set(LABELS)
    unknown_rels = rel_types - set(RELATIONSHIPS)
    if unknown_labels:
        raise CypherRejected(f"unknown labels: {sorted(unknown_labels)}")
    if unknown_rels:
        raise CypherRejected(f"unknown relationships: {sorted(unknown_rels)}")

    match = _LIMIT.search(text)
    if match is None:
        return text + f"\nLIMIT {cap}"
    if int(match.group(1)) > cap:
        raise CypherRejected(f"LIMIT exceeds {cap}")
    return text
