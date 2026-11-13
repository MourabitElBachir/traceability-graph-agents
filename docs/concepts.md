# Concepts

Canonical copy: [README](../README.md#2-concepts-in-plain-language). This page is the teaching split.

All names below are fictional. The running chain is wheat `BLE-0457` → flour `FAR-118` → biscuits `BIS-031`, certificate `CERT-77`.

## Ontology

An ontology is a shared vocabulary: kinds of things, relations, and a few rules. It is not a product you install.

OWL is a language for that vocabulary. RDF is the triple data model. Turtle is a text syntax. Protégé is an editor. This repository stores the vocabulary in `ontology/traceability.ttl` and reads it with rdflib. You do not need Protégé to run the demo.

## Knowledge graph and property graph

The ontology is the empty vocabulary. The knowledge graph is the vocabulary plus facts (this lot, this mill, this certificate). Neo4j stores those facts as a property graph: nodes, relationships, and properties. That shape fits “what is downstream of `BLE-0457`?”.

## GS1 EPCIS

EPCIS events answer what, when, where, and why. A process step here has an event time, a site, and a business step (`commissioning` or `transformation`). Certificates are extra nodes because EPCIS does not treat them as core events. Demo GLNs and GTINs are prefixed `DEMO-` and are not real GS1 keys.

## GraphRAG and plain RAG

Plain RAG searches similar text. It will not reliably list `FAR-118` and `BIS-031` as the children of `BLE-0457`. GraphRAG walks the graph for that, and uses vectors only for prose such as the mill audit.

## LangChain and LangGraph

LangChain builds the prompts (text-to-Cypher, short narrative). LangGraph runs the supervisor, the specialist nodes, the checkpointer, and the interrupt before a recall is issued.

## MCP and A2A

MCP exposes `trace_lot`, `check_certificates`, and `search_documents` to any MCP client. A2A here is a small card (`a2a-minimal-0.1`) plus `POST /a2a/tasks`. It is labelled as a subset so it is not mistaken for a full agent protocol.

## Worked example

Ferme des Collines commissions `BLE-0457`. Moulin du Val mills `FAR-118`. Fournil Lumière bakes `BIS-031`. Organisme Horizon’s certificate `CERT-77` covers all three and is valid on 2026-11-13. Épicerie Rive receives the biscuits. A separate mixed flour (`FAR-221`) and an oil lot with no source (`OIL-009`) exist so compliance has anomalies that do not touch the biscuit line.
