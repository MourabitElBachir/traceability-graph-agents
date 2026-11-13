# Retrieval

Canonical copy: [README §8](../README.md#8-retrieval).

## Hybrid GraphRAG

1. Exact walk for lots and certificates (`lineage.py`).
2. Vector plus lexical score over document chunks. In mock mode the embedding is a 64-d hash, mixed with token overlap so “mill audit” and “mixed” hit `DOC-AUDIT-MILL`.
3. Chunks carry entity ids. A caller only sees a chunk when every lot id on it is in their visible set (regulators and auditors see all).

Neo4j path: index `chunk_embedding`, cosine. Agents still use the shared Python walk so answers match CI.

## Text-to-Cypher guardrails

`draft_cypher` builds a prompt with `schema_card()` (LangChain `ChatPromptTemplate`). Mock mode does not call a model; it emits a template. `validate_cypher` then:

- rejects empty text, comments, and `;`
- rejects `CREATE`, `MERGE`, `DELETE`, `SET`, `DROP`, `CALL`, and the other write keywords
- requires a single `MATCH` … `RETURN`
- checks labels and relationship types against `graph/schema.py`
- caps `LIMIT` at 50

Rows that mention a lot the caller cannot see are dropped.

The hero query that returns `BLE-0457`, `FAR-118`, `BIS-031`, `CERT-77` is accepted and executed in memory mode.
