# ADR 0005 — Mock LLM as the default gateway

## Status

Accepted.

## Context

The repo must run in CI and on a laptop with no API key, and must not invent lot ids.

## Decision

`LLM_MODE=mock` by default. The mock returns a fixed sentence. `LLM_MODE=openai` posts to an OpenAI-compatible `/chat/completions`. Narratives that contain unknown ids are dropped. `AGRITRACE_AS_OF=2026-11-13` freezes certificate expiry.

## Consequences

Eval measures tools, not a hosted model. Switching dimension of embeddings requires a new vector index.
