"""Containment plans for BLE-0457: block, quarantine, or recall, then a what-if."""

from __future__ import annotations

import json

from agritrace.data.generator import HERO_BISCUITS, HERO_FLOUR, HERO_WHEAT
from agritrace.mcp.server import TOOLS, optimize_recall_plan
from agritrace.optimization.model import LotView, Parameters, Problem, action_options
from agritrace.optimization.solve import compare_plans
from agritrace.optimization.solvers import solve
from agritrace.service import TraceService


def _by_lot(plan: dict[str, object]) -> dict[str, dict[str, object]]:
    return {str(row["lot_id"]): row for row in plan["decisions"]}  # type: ignore[index]


def test_baseline_plan_on_the_worked_example(engine: TraceService) -> None:
    plans = compare_plans(engine.store, HERO_WHEAT, engine.settings.as_of, [("baseline", {})])
    highs = compare_plans(engine.store, HERO_WHEAT, engine.settings.as_of, [("baseline", {})], engine="highs")
    plan = plans[0]
    assert plan["status"] == "OPTIMAL"
    assert plan["optimality_gap"] == 0.0
    decisions = _by_lot(plan)
    assert decisions[HERO_WHEAT]["action"] == "block"
    assert decisions[HERO_FLOUR]["action"] == "quarantine"
    assert decisions[HERO_BISCUITS]["action"] == "recall"
    assert decisions[HERO_BISCUITS]["delivered"] is True
    assert plan["objective_eur"] == round(
        decisions[HERO_WHEAT]["cost_eur"] + decisions[HERO_FLOUR]["cost_eur"] + decisions[HERO_BISCUITS]["cost_eur"],
        2,
    )
    assert highs[0]["objective_eur"] == plan["objective_eur"]
    assert [row["action"] for row in highs[0]["decisions"]] == [row["action"] for row in plan["decisions"]]


def test_what_if_lab_and_delivery_change_the_plan(engine: TraceService) -> None:
    plans = compare_plans(
        engine.store,
        HERO_WHEAT,
        engine.settings.as_of,
        [
            ("baseline", {}),
            ("no_lab_capacity", {"lab_tests_per_day": 0}),
            ("biscuits_not_delivered", {"delivered": {HERO_BISCUITS: False}}),
        ],
    )
    baseline, no_lab, not_delivered = (_by_lot(plan) for plan in plans)
    assert no_lab[HERO_FLOUR]["action"] == "redirect"
    assert no_lab[HERO_FLOUR]["channel_id"] == "feed"
    assert not_delivered[HERO_BISCUITS]["action"] == "block"
    assert plans[1]["objective_eur"] != plans[0]["objective_eur"]
    assert baseline[HERO_BISCUITS]["action"] == "recall"


def test_high_risk_cannot_be_only_quarantined() -> None:
    lot = LotView("LOT-X", "SITE-VAL", 1000, False, 0.95, 1.0, ("Organic Horizon",))
    options = {option.action: option for option in action_options(lot, Parameters())}
    assert options["quarantine"].feasible is False
    assert options["redirect"].feasible is False
    assert options["block"].feasible is True
    assert options["recall"].feasible is True


def test_expired_certificate_blocks_organic_redirect() -> None:
    lot = LotView("LOT-Y", "SITE-VAL", 1000, False, 0.20, 1.0, ())
    options = {option.action: option for option in action_options(lot, Parameters())}
    assert options["redirect"].feasible is True
    assert options["redirect"].channel_id == "feed"


def test_lab_slot_goes_to_the_lot_that_saves_more() -> None:
    from agritrace.optimization.model import Channel

    parameters = Parameters(
        lab_tests_per_day=1,
        deadline_days=1,
        test_lead_days=1,
        test_fee_eur=10,
        hold_eur_per_kg=0,
        quarantine_residual=0,
        channels=(Channel("feed", "SITE-HALLE", (), loss_eur_per_kg=10, logistics_eur_per_kg=1, risk_eur_per_unit=10),),
    )
    cheap_to_test = LotView("LOT-A", "SITE-VAL", 100, False, 0.10, 5.0, ("Organic Horizon",))
    expensive_to_test = LotView("LOT-B", "SITE-LUMIERE", 100, False, 0.10, 1.0, ("Organic Horizon",))
    problem = Problem("LOT-A", [cheap_to_test, expensive_to_test], parameters, "one-slot")
    plan = solve(problem, "cpsat")
    decisions = _by_lot(plan)
    assert decisions["LOT-A"]["action"] == "quarantine"
    assert decisions["LOT-B"]["action"] != "quarantine"
    assert "Lab test capacity is fully used" in " ".join(plan["binding_constraints"])


def test_agent_keeps_human_approval(engine: TraceService) -> None:
    pending = engine.ask("What is the downstream recall impact of BLE-0457?", "opt-recall")
    assert pending.status == "needs_approval"
    assert "pending human approval" in pending.answer
    assert "Prescriptive plan" in pending.answer
    assert "action block" in pending.answer
    assert "action recall" in pending.answer
    assert "Recall issued" not in pending.answer
    approved = engine.ask("", "opt-recall", human_decision="approve")
    assert "Recall issued for BLE-0457" in approved.answer


def test_mcp_optimize_tool(engine: TraceService) -> None:
    from agritrace.mcp import server as mcp_server

    mcp_server._SERVICE = engine
    payload = json.loads(optimize_recall_plan(HERO_WHEAT))
    assert payload["decisions"][0]["lot_id"] == HERO_WHEAT
    assert "optimize_recall_plan" in TOOLS
    denied = json.loads(optimize_recall_plan(HERO_WHEAT, actor_id="ACT-RIVE"))
    assert "error" in denied
