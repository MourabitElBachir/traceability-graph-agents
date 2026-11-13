"""Agent card served at /.well-known/agent-card.json."""

from __future__ import annotations

from typing import Any


def agent_card(base_url: str) -> dict[str, Any]:
    root = base_url.rstrip("/")
    return {
        "protocol": "a2a-minimal-0.1",
        "name": "AgriTrace recall assistant",
        "description": (
            "Teaching subset of an agent-to-agent card for a fictional agrifood "
            "traceability assistant. It is not a certified A2A implementation."
        ),
        "url": f"{root}/a2a/tasks",
        "version": "0.1.0",
        "capabilities": {"streaming": False, "humanInTheLoop": True},
        "defaultInputModes": ["text"],
        "defaultOutputModes": ["text"],
        "skills": [
            {
                "id": "trace_lot",
                "name": "Trace a lot",
                "description": "Upstream or downstream lineage. Running example: BIS-031 to FAR-118 to BLE-0457.",
            },
            {
                "id": "check_certificates",
                "name": "Check certificates",
                "description": "Validity of CERT-77 on the biscuit line, and detection of expired certificates.",
            },
            {
                "id": "search_documents",
                "name": "Search documents",
                "description": "Hybrid retrieval over fictional certificate and audit text.",
            },
        ],
    }
