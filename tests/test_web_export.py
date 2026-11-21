"""The web demo JSON is produced by the real cost model."""

from __future__ import annotations

import json

from scripts.export_web_scenarios import catalog


def test_export_matches_the_worked_example() -> None:
    payload = catalog()
    case = payload["cases"]["BLE-0457"]
    baseline = next(row for row in case["scenarios"] if row["key"] == "2|true|0.6")
    actions = {row["lotId"]: row["action"] for row in baseline["decisions"]}
    assert actions == {"BLE-0457": "block", "FAR-118": "quarantine", "BIS-031": "recall"}
    assert baseline["totalEur"] == 27683.0
    assert baseline["naiveRecallEur"] > baseline["totalEur"]
    assert baseline["savingsEur"] == round(baseline["naiveRecallEur"] - baseline["totalEur"], 2)
    assert "Épicerie Rive" in case["impact"]["summary"]
    assert "3 lots touchés" in case["impact"]["summary"]
    no_lab = next(row for row in case["scenarios"] if row["key"] == "0|true|0.6")
    flour = next(row for row in no_lab["decisions"] if row["lotId"] == "FAR-118")
    assert flour["action"] == "redirect"
    raw = json.dumps(payload)
    for banned in ("CP-SAT", "Cypher", "GraphRAG", "solver"):
        assert banned not in raw
