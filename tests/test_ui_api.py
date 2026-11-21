"""Plain-language endpoints used by the optional live screen."""

from __future__ import annotations

from fastapi.testclient import TestClient

from agritrace.service import TraceService


def test_ui_plan_and_approve(engine: TraceService) -> None:
    from agritrace.api.main import app

    app.state.service = engine
    client = TestClient(app)
    impact = client.get("/ui/impact/BLE-0457")
    assert impact.status_code == 200
    assert "Épicerie Rive" in impact.json()["summary"]
    plan = client.post(
        "/ui/plan",
        json={
            "lot_id": "BLE-0457",
            "lab_tests_per_day": 2,
            "biscuits_delivered": True,
            "risk_threshold": 0.6,
        },
    )
    body = plan.json()
    assert plan.status_code == 200
    assert body["totalEur"] == 27683.0
    assert body["savingsEur"] == round(body["naiveRecallEur"] - body["totalEur"], 2)
    approved = client.post(
        "/ui/approve",
        json={
            "lot_id": "BLE-0457",
            "decision": "approve",
            "comment": "Je confirme le plan.",
            "reason": "contamination",
        },
    )
    assert approved.status_code == 200
    assert approved.json()["decision"] == "approve"
