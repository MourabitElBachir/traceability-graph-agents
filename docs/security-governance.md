# Security and governance

Canonical copy: [README §10](../README.md#10-security-and-governance).

## Data governance

- **Lineage.** Nodes are loaded from the SQLite extract and tagged `source_system=erp-sqlite`.
- **Catalog.** The ontology file is the catalog. `GET /ontology` returns classes and version.
- **Versioning.** `owl:versionInfo "0.1.0"` is copied to `ontology_version` on ingest.
- **Quality.** `check_quality` fails the load on dangling ids, inverted certificate dates, and empty documents. Expired `CERT-78` and the empty-input press step are findings, not load errors: they are the scenario.

## Access

`security/rbac.py` computes visible lots:

- retailer: lots shipped to their site, plus upstream (Épicerie Rive sees `BIS-031`, `FAR-118`, `BLE-0457`, not `OIL-009`);
- producer: lots they commissioned, plus downstream (Ferme des Collines sees the biscuit line, not `FAR-221`);
- processor and distributor: lots they touch, plus upstream and downstream;
- certifier: lots on certificates they issued, plus downstream;
- auditor: lots at sites they audited;
- regulator: all.

`read_cypher` is limited to auditor and regulator. Approving a recall is limited to the regulator. Missing `X-Actor-Id` is the regulator only while `AGRITRACE_DEMO_OPEN=1`.

## Secrets, personal data, model guardrails

No API key is required. `.env` is ignored. The Compose password fallback is local only.

The seed has no real persons. Questions are written to the demo audit log; production should redact them and set a retention period. Mock mode does not send text to a provider.

Injection patterns are flagged and the narrative model is skipped. Cypher must be a read. Answers cite tool ids. A narrative that invents an id is discarded.

## Human oversight, gateway, monitoring, EU AI Act notes

A recall stays `needs_approval` until a person resumes the thread. The LLM gateway is `LLM_MODE` plus an OpenAI-compatible base URL, temperature 0, behind those guards.

OpenTelemetry spans cover ingest, trace, search, and ask. Export is off by default.

A recall that can remove food from sale is an action that needs a human. This repository is a demo, not a conformity assessment. The notes are engineering controls, not legal advice.

The decision log is `GET /audit` and optional `AUDIT_LOG_PATH`. It is process-local unless the path is set.
