# ADR 0003 — MCP tools and a minimal A2A card

## Status

Accepted as a teaching surface.

## Context

Other assistants should call trace and certificate checks without scraping the UI. A second agent should be able to discover this one.

## Decision

MCP tools: `trace_lot`, `check_certificates`, `search_documents`. Separately, publish `/.well-known/agent-card.json` with `protocol: a2a-minimal-0.1` and accept `POST /a2a/tasks`. The card says it is not a full A2A stack.

## Consequences

Two protocols, clearly scoped. A complete A2A task model is not implemented.
