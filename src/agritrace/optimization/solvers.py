"""CP-SAT (primary) and HiGHS MIP on the same integer-cent formulation."""

from __future__ import annotations

from typing import Any

from ortools.sat.python import cp_model

from agritrace.optimization.model import Action, ActionOption, LotView, Problem, action_options


def _columns(problem: Problem) -> list[tuple[LotView, ActionOption]]:
    columns: list[tuple[LotView, ActionOption]] = []
    for lot in problem.lots:
        for option in action_options(lot, problem.parameters):
            if option.feasible:
                columns.append((lot, option))
    return columns


def _empty_plan(problem: Problem, solver: str) -> dict[str, Any]:
    return {
        "solver": solver,
        "status": "INFEASIBLE",
        "objective_eur": None,
        "optimality_gap": None,
        "decisions": [],
        "binding_constraints": ["No feasible action remains for at least one lot."],
        "scenario": problem.scenario,
        "root_lot_id": problem.root_lot_id,
    }


def _decisions(
    problem: Problem,
    chosen: dict[str, Action],
    solver: str,
    status: str,
    objective_cents: int,
    gap: float,
) -> dict[str, Any]:
    parameters = problem.parameters
    decisions: list[dict[str, Any]] = []
    binding: list[str] = []
    quarantine_kg: dict[str, int] = {}
    quarantine_tests = 0
    for lot in problem.lots:
        options = action_options(lot, parameters)
        picked = next(option for option in options if option.action == chosen[lot.lot_id])
        feasible = [option for option in options if option.feasible]
        cheapest = min(feasible, key=lambda option: option.cost_cents)
        removed = [option for option in options if not option.feasible and option.cost_cents < picked.cost_cents]
        why = picked.reason
        if lot.risk >= parameters.risk_threshold and not lot.delivered:
            why = (
                f"Risk {lot.risk:.2f} is at or above {parameters.risk_threshold:.2f}, "
                f"so the choice is block or recall. {picked.action} costs less."
            )
        if removed:
            why = removed[0].reason + " Chosen " + picked.action + f" at {picked.cost_cents / 100:.2f} EUR."
            for option in removed:
                if option.reason not in binding:
                    binding.append(option.reason)
        elif picked.action != cheapest.action:
            why = (
                f"Shared capacity kept {picked.action} ({picked.cost_cents / 100:.2f} EUR) ahead of {cheapest.action}."
            )
        decisions.append(
            {
                "lot_id": lot.lot_id,
                "site_id": lot.site_id,
                "quantity_kg": lot.quantity_kg,
                "risk": lot.risk,
                "delivered": lot.delivered,
                "action": picked.action,
                "channel_id": picked.channel_id,
                "cost_eur": round(picked.cost_cents / 100, 2),
                "breakdown_eur": picked.breakdown_eur,
                "reason": why,
                "alternatives": [
                    {
                        "action": option.action,
                        "feasible": option.feasible,
                        "cost_eur": round(option.cost_cents / 100, 2),
                        "reason": option.reason,
                    }
                    for option in options
                ],
            }
        )
        if picked.action == "quarantine":
            quarantine_kg[lot.site_id] = quarantine_kg.get(lot.site_id, 0) + lot.quantity_kg
            quarantine_tests += 1
    for site_id, used in quarantine_kg.items():
        cap = parameters.site_quarantine_kg.get(site_id, 0)
        if used == cap:
            binding.append(f"Quarantine capacity at {site_id} is fully used ({cap} kg).")
    if quarantine_tests == parameters.lab_slots and parameters.lab_slots > 0:
        binding.append(f"Lab test capacity is fully used ({parameters.lab_slots} tests).")
    if status == "OPTIMAL" and "Proven optimal." not in binding:
        binding.append("Proven optimal.")
    return {
        "solver": solver,
        "status": status,
        "objective_eur": round(objective_cents / 100, 2),
        "optimality_gap": gap,
        "decisions": decisions,
        "binding_constraints": binding,
        "scenario": problem.scenario,
        "root_lot_id": problem.root_lot_id,
    }


def solve_cpsat(problem: Problem) -> dict[str, Any]:
    columns = _columns(problem)
    by_lot: dict[str, list[tuple[int, ActionOption]]] = {lot.lot_id: [] for lot in problem.lots}
    model = cp_model.CpModel()
    variables: list[cp_model.IntVar] = []
    for index, (lot, option) in enumerate(columns):
        var = model.new_bool_var(f"{lot.lot_id}_{option.action}")
        variables.append(var)
        by_lot[lot.lot_id].append((index, option))
    if any(not items for items in by_lot.values()):
        return _empty_plan(problem, "cp-sat")
    for _lot_id, items in by_lot.items():
        model.add(sum(variables[index] for index, _option in items) == 1)
    _add_shared_capacity(model, problem, columns, variables)
    model.minimize(sum(option.cost_cents * variables[index] for index, (_lot, option) in enumerate(columns)))
    solver = cp_model.CpSolver()
    solver.parameters.num_search_workers = 1
    code = solver.solve(model)
    if code not in {cp_model.OPTIMAL, cp_model.FEASIBLE}:
        return _empty_plan(problem, "cp-sat")
    chosen = {
        lot.lot_id: option.action for index, (lot, option) in enumerate(columns) if solver.value(variables[index]) == 1
    }
    objective = int(round(solver.objective_value))
    bound = solver.best_objective_bound
    gap = 0.0 if code == cp_model.OPTIMAL else abs(objective - bound) / max(abs(objective), 1)
    status = "OPTIMAL" if code == cp_model.OPTIMAL else "FEASIBLE"
    return _decisions(problem, chosen, "cp-sat", status, objective, gap)


def _add_shared_capacity(
    model: cp_model.CpModel,
    problem: Problem,
    columns: list[tuple[LotView, ActionOption]],
    variables: list[Any],
) -> None:
    parameters = problem.parameters
    tests = [variables[index] for index, (lot, option) in enumerate(columns) if option.action == "quarantine"]
    if tests:
        model.add(sum(tests) <= parameters.lab_slots)
    sites = {lot.site_id for lot, option in columns if option.action == "quarantine"}
    for site_id in sites:
        terms = [
            lot.quantity_kg * variables[index]
            for index, (lot, option) in enumerate(columns)
            if option.action == "quarantine" and lot.site_id == site_id
        ]
        cap = parameters.site_quarantine_kg.get(site_id, 0)
        if terms:
            model.add(sum(terms) <= cap)


def solve_highs(problem: Problem) -> dict[str, Any]:
    import highspy

    columns = _columns(problem)
    by_lot: dict[str, list[int]] = {lot.lot_id: [] for lot in problem.lots}
    if not columns or any(not any(lot.lot_id == key for lot, _option in columns) for key in by_lot):
        # Re-check per lot feasibility the same way as CP-SAT.
        if any(not [pair for pair in columns if pair[0].lot_id == lot.lot_id] for lot in problem.lots):
            return _empty_plan(problem, "highs")
    import os

    saved = os.dup(1)
    devnull = os.open(os.devnull, os.O_WRONLY)
    try:
        os.dup2(devnull, 1)
        highs = highspy.Highs()
    finally:
        os.dup2(saved, 1)
        os.close(saved)
        os.close(devnull)
    highs.setOptionValue("output_flag", False)
    variables = []
    for lot, option in columns:
        variables.append(highs.addBinary(obj=float(option.cost_cents), name=f"{lot.lot_id}_{option.action}"))
        by_lot[lot.lot_id].append(len(variables) - 1)
    for indexes in by_lot.values():
        if not indexes:
            return _empty_plan(problem, "highs")
        expr = variables[indexes[0]]
        for index in indexes[1:]:
            expr = expr + variables[index]
        highs.addConstr(expr == 1)
    quarantine_idx = [index for index, (_lot, option) in enumerate(columns) if option.action == "quarantine"]
    if quarantine_idx:
        expr = variables[quarantine_idx[0]]
        for index in quarantine_idx[1:]:
            expr = expr + variables[index]
        highs.addConstr(expr <= problem.parameters.lab_slots)
    sites = {lot.site_id for lot, option in columns if option.action == "quarantine"}
    for site_id in sites:
        terms = [
            (index, lot.quantity_kg)
            for index, (lot, option) in enumerate(columns)
            if option.action == "quarantine" and lot.site_id == site_id
        ]
        if not terms:
            continue
        expr = terms[0][1] * variables[terms[0][0]]
        for index, qty in terms[1:]:
            expr = expr + qty * variables[index]
        highs.addConstr(expr <= problem.parameters.site_quarantine_kg.get(site_id, 0))
    highs.minimize()
    status = str(highs.getModelStatus()).split(".")[-1]
    if status not in {"kOptimal", "kFeasible"}:
        return _empty_plan(problem, "highs")
    values = list(highs.getSolution().col_value)
    chosen: dict[str, Action] = {}
    for index, (lot, option) in enumerate(columns):
        if values[index] > 0.5:
            chosen[lot.lot_id] = option.action
    if len(chosen) != len(problem.lots):
        return _empty_plan(problem, "highs")
    objective = int(round(highs.getObjectiveValue()))
    label = "OPTIMAL" if status == "kOptimal" else "FEASIBLE"
    gap = 0.0 if label == "OPTIMAL" else None
    return _decisions(problem, chosen, "highs", label, objective, gap if gap is not None else 0.0)


def solve(problem: Problem, engine: str = "cpsat") -> dict[str, Any]:
    if engine == "cpsat":
        return solve_cpsat(problem)
    if engine == "highs":
        return solve_highs(problem)
    raise ValueError(f"unknown solver {engine}; use cpsat or highs")


__all__ = ["solve", "solve_cpsat", "solve_highs"]
