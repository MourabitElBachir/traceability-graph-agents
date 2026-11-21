"""Print the optimal containment plan for BLE-0457 and two what-if plans."""

from __future__ import annotations

from agritrace.data.generator import HERO_WHEAT
from agritrace.optimization.solve import compare_plans
from agritrace.service import build_service


def _print_plan(plan: dict[str, object]) -> None:
    print(
        f"scenario={plan['scenario']} solver={plan['solver']} status={plan['status']} "
        f"cost={plan['objective_eur']} EUR gap={plan['optimality_gap']}"
    )
    decisions = plan["decisions"]
    assert isinstance(decisions, list)
    for row in decisions:
        print(
            f"  {row['lot_id']}: {row['action']} {row['cost_eur']} EUR "
            f"at {row['site_id']} ({row['quantity_kg']} kg, risk {row['risk']})"
        )
        print(f"    {row['reason']}")
    binding = plan["binding_constraints"]
    assert isinstance(binding, list)
    for item in binding:
        print(f"  constraint: {item}")


def main() -> None:
    service = build_service()
    as_of = service.settings.as_of
    print("Recall containment optimizer")
    print("Contaminated lot BLE-0457. Downstream from the graph: FAR-118, BIS-031. Certificate CERT-77.")
    plans = compare_plans(
        service.store,
        HERO_WHEAT,
        as_of,
        [
            ("baseline", {}),
            ("no_lab_capacity", {"lab_tests_per_day": 0}),
            ("biscuits_not_delivered", {"delivered": {"BIS-031": False}}),
        ],
    )
    highs = compare_plans(service.store, HERO_WHEAT, as_of, [("baseline", {})], engine="highs")
    _print_plan(plans[0])
    print(
        f"HiGHS MIP on the same baseline: {highs[0]['objective_eur']} EUR "
        f"status={highs[0]['status']} actions={[row['action'] for row in highs[0]['decisions']]}"
    )
    print("What-if comparison (CP-SAT):")
    for plan in plans:
        actions = ", ".join(f"{row['lot_id']}={row['action']}" for row in plan["decisions"])
        print(f"  {plan['scenario']}: {plan['objective_eur']} EUR ({actions})")


if __name__ == "__main__":
    main()
