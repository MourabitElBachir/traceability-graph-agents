# ADR 0001 — Neo4j for the lineage graph

## Status

Accepted for this portfolio. The vocabulary stays OWL.

## Context

Recall and trace are path questions. `BLE-0457` becomes `FAR-118` and then `BIS-031`.

## Decision

Project the ERP extract into a property graph. Uniqueness constraints on `id`. Derived `INPUT_OF` edges for variable-length walks. OWL file remains the versioned vocabulary, not the instance store.

## Consequences

Cypher is readable for the hero query. Instance data is loaded by Python, so a Neo4j-only rule engine is future work. CI uses the same lineage functions in memory.
