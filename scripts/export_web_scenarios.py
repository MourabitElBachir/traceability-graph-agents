"""Write the precomputed plans the web demo reads. No network and no secrets."""

from __future__ import annotations

import json
from pathlib import Path

from agritrace.optimization.present import impact_view, present_case
from agritrace.service import build_service

LAB_STEPS = [0, 1, 2, 4]
RISK_STEPS = [0.4, 0.6, 0.8]
LOTS = ["BLE-0457", "FAR-118", "BIS-031"]
REASONS = [
    {"id": "contamination", "fr": "Contamination", "en": "Contamination"},
    {"id": "expired", "fr": "Certificat expiré", "en": "Expired certificate"},
    {"id": "allergen", "fr": "Allergène non déclaré", "en": "Undeclared allergen"},
]


def catalog() -> dict[str, object]:
    service = build_service()
    as_of = service.settings.as_of
    cases: dict[str, object] = {}
    for lot_id in LOTS:
        impact = impact_view(service.store, lot_id, as_of)
        scenarios = []
        if lot_id == "BLE-0457":
            for lab in LAB_STEPS:
                for delivered in (True, False):
                    for risk in RISK_STEPS:
                        changes: dict[str, object] = {
                            "lab_tests_per_day": lab,
                            "risk_threshold": risk,
                            "delivered": {"BIS-031": delivered},
                        }
                        plan = present_case(service.store, lot_id, as_of, changes)
                        plan["key"] = f"{lab}|{str(delivered).lower()}|{risk}"
                        scenarios.append(plan)
        else:
            plan = present_case(service.store, lot_id, as_of, {})
            plan["key"] = "baseline"
            scenarios.append(plan)
        cases[lot_id] = {"impact": impact, "scenarios": scenarios}
    return {
        "asOf": as_of.isoformat(),
        "defaultLotId": "BLE-0457",
        "lots": [
            {"id": "BLE-0457", "product": "Blé tendre"},
            {"id": "FAR-118", "product": "Farine"},
            {"id": "BIS-031", "product": "Biscuits"},
        ],
        "reasons": REASONS,
        "labSteps": LAB_STEPS,
        "riskSteps": RISK_STEPS,
        "cases": cases,
    }


def main() -> None:
    root = Path(__file__).resolve().parents[1]
    target = root / "web" / "public" / "data" / "scenarios.json"
    target.parent.mkdir(parents=True, exist_ok=True)
    payload = catalog()
    target.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(f"wrote {target}")


if __name__ == "__main__":
    main()
