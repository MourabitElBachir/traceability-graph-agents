# ADR 0002 — LangGraph for the workflow

## Status

Accepted.

## Context

A recall must pause for a person. A single prompt cannot hold that pause.

## Decision

LangGraph `StateGraph` with a supervisor and specialist nodes. `MemorySaver` checkpoints the thread. `interrupt` runs after the proposal is written and before “Recall issued”.

LangChain is limited to prompt templates.

## Consequences

The route in mock mode is keywords, so tests are stable. The checkpointer is in-process only.
