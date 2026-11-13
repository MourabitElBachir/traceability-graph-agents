# ADR 0006 — SQL stays the system of record

## Status

Accepted.

## Context

Lots and shipments are born in an ERP. A graph is a projection for questions.

## Decision

Model an ERP schema and round-trip every load through SQLite before the graph. Documents live in SQL too, then become chunks.

## Consequences

Postgres is the intended hosted engine; only SQLite is wired. The schema uses portable column types.
