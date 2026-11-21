"""Facade used by the agent, the MCP tool, and the demo."""

from __future__ import annotations

from datetime import date
from typing import Any

from agritrace.optimization.model import LotView, Parameters, Problem, problem_from_store, replace_parameters
from agritrace.optimization.solvers import solve


def optimize_recall(
    store: Any,
    lot_id: str,
    as_of: date,
    *,
    engine: str = "cpsat",
    parameters: Parameters | None = None,
    scenario: str = "baseline",
) -> dict[str, Any]:
    problem = problem_from_store(store, lot_id, as_of, parameters)
    problem.scenario = scenario
    return solve(problem, engine)


def compare_plans(
    store: Any,
    lot_id: str,
    as_of: date,
    scenarios: list[tuple[str, dict[str, Any]]],
    *,
    engine: str = "cpsat",
) -> list[dict[str, Any]]:
    """What-if: same impacted lots, different capacities, deadlines, or delivery flags."""

    base = problem_from_store(store, lot_id, as_of, Parameters())
    plans: list[dict[str, Any]] = []
    for name, changes in scenarios:
        forced = changes.get("delivered")
        parameter_changes = {key: value for key, value in changes.items() if key != "delivered"}
        parameters = replace_parameters(base.parameters, **parameter_changes)
        lots = base.lots
        if isinstance(forced, dict):
            lots = [
                LotView(
                    lot_id=lot.lot_id,
                    site_id=lot.site_id,
                    quantity_kg=lot.quantity_kg,
                    delivered=bool(forced.get(lot.lot_id, lot.delivered)),
                    risk=lot.risk,
                    value_eur_per_kg=lot.value_eur_per_kg,
                    valid_schemes=lot.valid_schemes,
                )
                for lot in base.lots
            ]
        plans.append(solve(Problem(base.root_lot_id, lots, parameters, name), engine))
    return plans
