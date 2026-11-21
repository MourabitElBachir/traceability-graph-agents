"""Plain-language view of a plan. No tool names, for the quality-manager screens."""

from __future__ import annotations

from datetime import date
from typing import Any

from agritrace.optimization.model import recall_everything_eur
from agritrace.optimization.solve import build_scenario
from agritrace.optimization.solvers import solve

PRODUCTS: dict[str, str] = {
    "BLE-0457": "Blé tendre",
    "FAR-118": "Farine",
    "BIS-031": "Biscuits",
    "FAR-221": "Farine mélangée",
    "BLE-0881": "Blé",
    "BLE-0902": "Blé",
    "OIL-009": "Huile",
}

SITES: dict[str, str] = {
    "SITE-COLLINES": "Ferme des Collines",
    "SITE-VAL": "Moulin du Val",
    "SITE-LUMIERE": "Fournil Lumière",
    "SITE-RIVE": "Épicerie Rive",
    "SITE-HALLE": "Halle du Marché",
    "SITE-DISTNORD": "DistriNord Logistique",
    "SITE-BRUME": "Ferme Brume",
    "SITE-SAULES": "Ferme des Saules",
    "SITE-PRESS": "Pressoir des Olivettes",
}

ACTIONS_FR: dict[str, str] = {
    "block": "Bloquer",
    "quarantine": "Quarantaine",
    "redirect": "Rediriger",
    "recall": "Rappeler",
}


def plain_why(row: dict[str, Any], threshold: float) -> str:
    action = str(row["action"])
    if row.get("delivered") and action == "recall":
        return "Ce lot est déjà arrivé chez un client. La seule mesure possible est le rappel."
    if action == "block" and float(row["risk"]) >= threshold:
        return "Le risque est élevé. Bloquer coûte moins cher qu’un rappel, car le lot n’est pas encore chez un client."
    if action == "quarantine":
        return "Le lot est encore sur place. Un contrôle coûte moins cher qu’un rappel."
    if action == "redirect":
        return (
            "Le laboratoire ne peut pas tout contrôler. "
            "L’envoyer vers un autre débouché coûte moins cher que de le détruire."
        )
    if action == "block":
        return "Le bloquer coûte moins cher que de le rappeler."
    return "Le rappel est la mesure la moins coûteuse parmi celles qui restent possibles."


def _summary(lots: list[dict[str, Any]]) -> str:
    sites = {str(lot["site"]) for lot in lots}
    delivered = [lot for lot in lots if lot["status"] == "livre"]
    n_lots = len(lots)
    n_sites = len(sites)
    n_del = len(delivered)
    lot_word = "lot touché" if n_lots == 1 else "lots touchés"
    site_word = "site" if n_sites == 1 else "sites"
    if n_del == 0:
        tail = "aucun n’est encore livré"
    elif n_del == 1:
        tail = f"1 déjà livré à {delivered[0]['customer']}"
    else:
        names = ", ".join(str(lot["customer"]) for lot in delivered)
        tail = f"{n_del} déjà livrés à {names}"
    return f"{n_lots} {lot_word} sur {n_sites} {site_word}, dont {tail}."


def present_case(store: Any, lot_id: str, as_of: date, changes: dict[str, Any] | None = None) -> dict[str, Any]:
    changes = changes or {}
    problem = build_scenario(store, lot_id, as_of, changes, "case")
    plan = solve(problem, "cpsat")
    threshold = problem.parameters.risk_threshold
    naive = recall_everything_eur(problem)
    total = float(plan["objective_eur"] or 0)
    decisions = []
    for row in plan["decisions"]:
        decisions.append(
            {
                "lotId": row["lot_id"],
                "product": PRODUCTS.get(str(row["lot_id"]), "Lot"),
                "site": SITES.get(str(row["site_id"]), str(row["site_id"])),
                "quantityKg": row["quantity_kg"],
                "delivered": row["delivered"],
                "action": row["action"],
                "actionLabel": ACTIONS_FR[str(row["action"])],
                "costEur": row["cost_eur"],
                "why": plain_why(row, threshold),
            }
        )
    return {
        "lotId": lot_id,
        "labTestsPerDay": problem.parameters.lab_tests_per_day,
        "biscuitsDelivered": next((lot.delivered for lot in problem.lots if lot.lot_id == "BIS-031"), False),
        "riskThreshold": threshold,
        "totalEur": total,
        "naiveRecallEur": naive,
        "savingsEur": round(naive - total, 2),
        "decisions": decisions,
    }


def impact_view(store: Any, lot_id: str, as_of: date) -> dict[str, Any]:
    problem = build_scenario(store, lot_id, as_of, {}, "impact")
    nodes: list[dict[str, Any]] = []
    edges: list[dict[str, str]] = []
    lots_payload: list[dict[str, Any]] = []
    previous: str | None = None
    for index, lot in enumerate(problem.lots):
        status = "livre" if lot.delivered else "stock"
        customer = SITES.get(lot.site_id, lot.site_id) if lot.delivered else ""
        node_id = lot.lot_id
        nodes.append(
            {
                "id": node_id,
                "label": f"{PRODUCTS.get(lot.lot_id, 'Lot')} {lot.lot_id}",
                "kind": "lot",
                "status": status,
                "x": 80 + index * 240,
                "y": 80,
            }
        )
        if previous:
            edges.append({"source": previous, "target": node_id})
        previous = node_id
        lots_payload.append(
            {
                "lotId": lot.lot_id,
                "product": PRODUCTS.get(lot.lot_id, "Lot"),
                "site": SITES.get(lot.site_id, lot.site_id),
                "status": status,
                "customer": customer or "—",
            }
        )
    if any(lot.delivered for lot in problem.lots):
        nodes.append(
            {
                "id": "customer-rive",
                "label": "Épicerie Rive",
                "kind": "customer",
                "status": "livre",
                "x": 80 + len(problem.lots) * 240,
                "y": 80,
            }
        )
        if previous:
            edges.append({"source": previous, "target": "customer-rive"})
    nodes.append(
        {
            "id": "healthy-halle",
            "label": "Halle du Marché",
            "kind": "customer",
            "status": "sain",
            "x": 80,
            "y": 240,
        }
    )
    source = (
        "Chemin relevé : blé BLE-0457, farine FAR-118, biscuits BIS-031. "
        "Le certificat de ce chemin est encore valable jusqu’au 31 décembre 2027."
        if lot_id == "BLE-0457"
        else f"Chemin relevé à partir du lot {lot_id}."
    )
    return {
        "lotId": lot_id,
        "summary": _summary(lots_payload),
        "source": source,
        "nodes": nodes,
        "edges": edges,
        "lots": lots_payload,
    }
