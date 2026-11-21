"""Prescriptive recall plans. The graph says what is impacted; a solver picks actions."""

from agritrace.optimization.solve import compare_plans, optimize_recall

__all__ = ["compare_plans", "optimize_recall"]
