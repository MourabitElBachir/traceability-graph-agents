# ADR 0004 — Hybrid retrieval

## Status

Accepted.

## Context

“What is upstream of `BIS-031`?” is a graph fact. “What did the mill audit say?” is prose.

## Decision

Deterministic walks for lineage and certificates. Vector search for chunks linked to those nodes. Text-to-Cypher is an extra read path with a validator, not the only path.

## Consequences

Answers for the hero chain do not depend on embedding quality. Free-form Cypher is limited to known templates in memory mode and to any guarded read on Neo4j.
