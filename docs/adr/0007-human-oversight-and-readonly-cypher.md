# ADR 0007 — Human approval and read-only Cypher

## Status

Accepted.

## Context

A recall recommendation can pull biscuits off a shelf. A generated query must not delete the graph.

## Decision

The recall route interrupts until `approve` or `reject`. Only the regulator can approve. `validate_cypher` rejects writes, multiple statements, unknown labels, and large `LIMIT`s. MCP does not expose free Cypher.

## Consequences

The demo cannot “just answer” a recall in one call. That is intentional.
