# Tools

Canonical copy: [README §8](../README.md#8-tools). Summary first, then one section per tool.

| Tool | Role here |
| --- | --- |
| Neo4j + Cypher + vector index | Queryable property graph |
| OWL / Turtle / rdflib | Versioned vocabulary |
| GS1 EPCIS (ideas) | What / when / where / why |
| SQLite, Postgres-shaped SQL | ERP system of record |
| Python 3.11 + Pydantic | Typed records |
| LangChain | Prompt templates |
| LangGraph | Supervisor, checkpoint, interrupt |
| MCP SDK | Three tools |
| A2A minimal | Agent card and task POST |
| FastAPI | HTTP API |
| Streamlit | Small UI |
| OpenTelemetry | Spans |
| LangSmith | Optional, off by default |
| OpenAI-compatible LLM and mock | Gateway |
| Docker Compose | Neo4j + API |
| pytest | Tests including the hero chain |
| GitHub Actions | Lint, types, tests, eval |
| uv, ruff, mypy | Environment, lint, types |
| Mermaid | Diagrams in the README |

## Neo4j, Cypher, vector index

A property graph. Chosen because downstream of `BLE-0457` is a walk, not a join. Files: `src/agritrace/graph/schema.py`, `src/agritrace/graph/neo4j_store.py`. Constraints require unique `id`. Index `chunk_embedding` is cosine over 64 mock dimensions.

```cypher
CREATE VECTOR INDEX chunk_embedding IF NOT EXISTS
FOR (c:Chunk) ON (c.embedding)
OPTIONS {indexConfig: { `vector.dimensions`: 64, `vector.similarity_function`: 'cosine' }}
```

Alternative: recursive SQL only. Kept as the ledger, not as the traversal API.

## OWL, Turtle, rdflib

The vocabulary is not a tool you “run”; OWL is the language, Turtle the syntax, rdflib the parser. File: `ontology/traceability.ttl`. Loader: `src/agritrace/ontology/loader.py`.

```turtle
agr:Lot a owl:Class ;
    rdfs:label "Lot"@en ;
    rdfs:comment "The running example is wheat BLE-0457, flour FAR-118, biscuits BIS-031."@en .
```

Alternative: a wiki table. It would not version as `owl:versionInfo`.

## GS1 EPCIS

Not a library in this repo. The process step carries `event_time` and `biz_step` so a supply-chain reader recognises commissioning and transformation. No official GS1 package is imported, and no real keys are used.

## SQLite and Postgres

`src/agritrace/data/schema.sql` and `erp.py`. Ingest always round-trips through SQLite. Postgres is the production shape of the same columns; the driver is not connected (roadmap).

```sql
CREATE TABLE lots (
    id TEXT PRIMARY KEY,
    product_id TEXT NOT NULL REFERENCES products(id),
    quantity REAL NOT NULL,
    produced_on TEXT NOT NULL,
    site_id TEXT NOT NULL REFERENCES sites(id)
);
```

## Python and Pydantic

`Lot`, `Certificate`, and `AskResponse` in `src/agritrace/models.py`. They are what SQL rows become before the graph load.

## LangChain

`ChatPromptTemplate` in `llm/provider.py` and `retrieval/text_to_cypher.py`. The prompt carries the schema card and forbids writes. The HTTP client, not a vendor chain, posts the messages when `LLM_MODE=openai`.

## LangGraph

`src/agritrace/agents/graph.py`. `StateGraph`, `MemorySaver`, `interrupt`, `Command`. The recall node stores the proposal; the next node interrupts.

## MCP

`src/agritrace/mcp/server.py`. SDK 2.x `MCPServer`. Tools: `trace_lot`, `check_certificates`, `search_documents`.

```python
TOOLS = {
    "trace_lot": trace_lot,
    "check_certificates": check_certificates,
    "search_documents": search_documents,
}
```

Alternative: a private JSON-RPC. MCP is the interop surface.

## A2A

`src/agritrace/a2a/card.py`. Protocol id `a2a-minimal-0.1`. `GET /.well-known/agent-card.json`, `POST /a2a/tasks`. Not a full task lifecycle.

## FastAPI

`src/agritrace/api/main.py`. `POST /ask` runs the graph. `POST /ask/resume` continues a recall. `POST /cypher` is guarded.

## Streamlit

`ui/streamlit_app.py`. Same service, actor picker, approve / reject.

## OpenTelemetry

`src/agritrace/observability/otel.py`. `configure_telemetry` supports `none`, `console`, and `otlp`. Default is none.

## LangSmith

No code dependency. `LANGCHAIN_TRACING_V2=true` plus `LANGCHAIN_API_KEY` lets LangChain emit traces. CI leaves this false.

## LLM gateway and mock

`src/agritrace/llm/provider.py`. `MockLLM` returns one sentence and invents no ids. `OpenAICompatibleLLM` posts to `/chat/completions`. Embeddings follow the same switch.

## Docker Compose

`compose.yaml`. Neo4j `5.26.0-community` with a healthcheck, API image depending on it, loopback ports, dev-only password fallback.

## pytest

`tests/test_hero_chain.py` and `tests/test_agents_security_api.py`. They lock `BLE-0457`, `FAR-118`, `BIS-031`, and `CERT-77`.

## GitHub Actions

`.github/workflows/ci.yml`. Python 3.11, ruff, mypy, pytest, eval, mock mode.

## uv, ruff, mypy

`pyproject.toml`. uv is optional for local 3.11. ruff line length 120. mypy `disallow_untyped_defs` on `src`.

## Mermaid

Diagrams in the README use a shared forest/wheat `themeVariables` block so GitHub renders them. SVG/PNG twins: `docs/assets/`, built by `scripts/render_assets.py`.
