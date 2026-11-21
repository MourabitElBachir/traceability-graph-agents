"""Decision data: lots from the graph become variables, rules become constraints.

Costs are integer cents so CP-SAT and HiGHS share one objective.
"""

from __future__ import annotations

from dataclasses import dataclass, field, replace
from datetime import date
from typing import Any, Literal

Action = Literal["block", "quarantine", "redirect", "recall"]
ACTIONS: tuple[Action, ...] = ("block", "quarantine", "redirect", "recall")


def cents(euros: float) -> int:
    return int(round(euros * 100))


@dataclass(frozen=True)
class Channel:
    channel_id: str
    site_id: str
    required_schemes: tuple[str, ...]
    loss_eur_per_kg: float
    logistics_eur_per_kg: float
    risk_eur_per_unit: float


@dataclass(frozen=True)
class Parameters:
    """Planning coefficients for the fictional fixture. Not a price list from a client."""

    risk_threshold: float = 0.60
    admin_eur: float = 50.0
    test_fee_eur: float = 600.0
    hold_eur_per_kg: float = 0.02
    quarantine_residual: float = 0.10
    brand_eur_per_risk_kg: float = 5.0
    recall_logistics_eur_per_kg: float = 0.30
    deadline_days: int = 5
    test_lead_days: int = 2
    lab_tests_per_day: int = 2
    site_quarantine_kg: dict[str, int] = field(
        default_factory=lambda: {
            "SITE-COLLINES": 5000,
            "SITE-VAL": 20000,
            "SITE-LUMIERE": 8000,
            "SITE-RIVE": 0,
            "SITE-HALLE": 4000,
        }
    )
    channels: tuple[Channel, ...] = (
        Channel(
            channel_id="organic_retail",
            site_id="SITE-HALLE",
            required_schemes=("Organic Horizon",),
            loss_eur_per_kg=0.15,
            logistics_eur_per_kg=0.05,
            risk_eur_per_unit=4.0,
        ),
        Channel(
            channel_id="feed",
            site_id="SITE-HALLE",
            required_schemes=(),
            loss_eur_per_kg=0.25,
            logistics_eur_per_kg=0.04,
            risk_eur_per_unit=0.30,
        ),
    )

    @property
    def lab_slots(self) -> int:
        if self.deadline_days < self.test_lead_days:
            return 0
        return max(self.lab_tests_per_day, 0) * max(self.deadline_days, 0)


@dataclass(frozen=True)
class LotView:
    lot_id: str
    site_id: str
    quantity_kg: int
    delivered: bool
    risk: float
    value_eur_per_kg: float
    valid_schemes: tuple[str, ...]


@dataclass(frozen=True)
class ActionOption:
    action: Action
    feasible: bool
    reason: str
    cost_cents: int
    breakdown_eur: dict[str, float]
    channel_id: str | None = None


@dataclass
class Problem:
    root_lot_id: str
    lots: list[LotView]
    parameters: Parameters
    scenario: str = "baseline"

    def with_parameters(self, parameters: Parameters, scenario: str) -> Problem:
        return Problem(self.root_lot_id, self.lots, parameters, scenario)


# Risk and value are planning inputs. Quantities, sites, delivery, and certificates come from the graph.
ECONOMICS: dict[str, dict[str, float]] = {
    "BLE-0457": {"risk": 0.92, "value_eur_per_kg": 0.40},
    "FAR-118": {"risk": 0.45, "value_eur_per_kg": 0.80},
    "BIS-031": {"risk": 0.88, "value_eur_per_kg": 2.50},
}


def _euros(**parts: float) -> tuple[int, dict[str, float]]:
    breakdown = {key: round(value, 2) for key, value in parts.items()}
    return cents(sum(parts.values())), breakdown


def action_options(lot: LotView, parameters: Parameters) -> list[ActionOption]:
    """Every action, with the rule that removes it when it is not allowed."""

    qty = lot.quantity_kg
    value = qty * lot.value_eur_per_kg
    options: list[ActionOption] = []

    block_cents, block_parts = _euros(product_loss=value, admin=parameters.admin_eur)
    options.append(
        ActionOption("block", True, "Always feasible when the lot is not already delivered.", block_cents, block_parts)
    )

    quarantine_ok = True
    quarantine_reason = "Test, hold, then keep a residual risk cost."
    if lot.delivered:
        quarantine_ok = False
        quarantine_reason = "Already delivered: quarantine is not available."
    elif lot.risk >= parameters.risk_threshold:
        quarantine_ok = False
        quarantine_reason = (
            f"Risk {lot.risk:.2f} is at or above {parameters.risk_threshold:.2f}: only block or recall is allowed."
        )
    elif parameters.lab_slots <= 0:
        quarantine_ok = False
        quarantine_reason = (
            f"Lab or deadline blocks testing (lead time {parameters.test_lead_days} days, "
            f"deadline {parameters.deadline_days} days, tests/day {parameters.lab_tests_per_day})."
        )
    elif parameters.site_quarantine_kg.get(lot.site_id, 0) <= 0:
        quarantine_ok = False
        quarantine_reason = f"{lot.site_id} has no quarantine capacity."
    residual = parameters.quarantine_residual * parameters.brand_eur_per_risk_kg * lot.risk * qty
    q_cents, q_parts = _euros(
        test=parameters.test_fee_eur,
        holding=parameters.hold_eur_per_kg * qty,
        residual_risk=residual,
    )
    options.append(ActionOption("quarantine", quarantine_ok, quarantine_reason, q_cents, q_parts))

    redirect_ok = True
    redirect_reason = "Redirect to the cheapest channel whose scheme rules are satisfied."
    channel: Channel | None = None
    best: tuple[int, dict[str, float], Channel] | None = None
    allowed = [
        item for item in parameters.channels if all(scheme in lot.valid_schemes for scheme in item.required_schemes)
    ]
    if lot.delivered:
        redirect_ok = False
        redirect_reason = "Already delivered: redirect is not available."
    elif lot.risk >= parameters.risk_threshold:
        redirect_ok = False
        redirect_reason = (
            f"Risk {lot.risk:.2f} is at or above {parameters.risk_threshold:.2f}: redirect is not allowed."
        )
    elif not allowed:
        redirect_ok = False
        redirect_reason = "No channel accepts this lot under the certificate rules."
    else:
        for item in allowed:
            cost, parts = _euros(
                lost_value=item.loss_eur_per_kg * qty,
                logistics=item.logistics_eur_per_kg * qty,
                residual_risk=item.risk_eur_per_unit * lot.risk * qty,
            )
            if best is None or cost < best[0]:
                best = (cost, parts, item)
        assert best is not None
        channel = best[2]
        redirect_reason = (
            f"Channel {channel.channel_id} at {channel.site_id}. "
            f"Required schemes: {', '.join(channel.required_schemes) or 'none'}."
        )
    r_cents = best[0] if best else cents(value + parameters.admin_eur)
    r_parts = best[1] if best else {"unavailable": 0.0}
    options.append(
        ActionOption(
            "redirect",
            redirect_ok,
            redirect_reason,
            r_cents,
            r_parts,
            None if channel is None else channel.channel_id,
        )
    )

    recall_cents, recall_parts = _euros(
        product_loss=value,
        admin=parameters.admin_eur,
        reverse_logistics=parameters.recall_logistics_eur_per_kg * qty,
    )
    if lot.delivered:
        recall_reason = "Shipment already delivered to a retailer: recall is the only legal action."
    else:
        recall_reason = "Full withdrawal plus reverse logistics."
    options.append(ActionOption("recall", True, recall_reason, recall_cents, recall_parts))

    if lot.delivered:
        for index, option in enumerate(options):
            if option.action != "recall":
                options[index] = ActionOption(
                    option.action,
                    False,
                    "Shipment already delivered to a retailer: only recall is allowed.",
                    option.cost_cents,
                    option.breakdown_eur,
                    option.channel_id,
                )
    elif lot.risk >= parameters.risk_threshold:
        for index, option in enumerate(options):
            if option.action in {"quarantine", "redirect"}:
                options[index] = ActionOption(
                    option.action,
                    False,
                    (
                        f"Risk {lot.risk:.2f} is at or above {parameters.risk_threshold:.2f}: "
                        "only block or recall is allowed."
                    ),
                    option.cost_cents,
                    option.breakdown_eur,
                    option.channel_id,
                )
    return options


def problem_from_store(store: Any, root_lot_id: str, as_of: date, parameters: Parameters | None = None) -> Problem:
    """Build variables from a trace. Works on the in-memory graph, so Neo4j is optional."""

    parameters = parameters or Parameters()
    trace = store.trace(root_lot_id, "downstream")
    downstream = [str(item) for item in trace["downstream_lot_ids"]]
    lot_ids = [root_lot_id, *[lot_id for lot_id in downstream if lot_id != root_lot_id]]
    index = store.require_index()
    dataset = index.dataset
    retailer_sites = {site.id for site in dataset.sites if index.actors[site.actor_id].role == "retailer"}
    delivered = {
        lot_id for shipment in dataset.shipments if shipment.to_site_id in retailer_sites for lot_id in shipment.lot_ids
    }
    lots: list[LotView] = []
    for lot_id in lot_ids:
        lot = index.lots[lot_id]
        economics = ECONOMICS.get(lot_id, {"risk": 0.50, "value_eur_per_kg": 1.0})
        schemes: list[str] = []
        for certificate in dataset.certificates:
            if lot_id not in certificate.covers_lot_ids or certificate.status != "valid":
                continue
            start = date.fromisoformat(certificate.valid_from)
            end = date.fromisoformat(certificate.valid_to)
            if start <= as_of <= end and certificate.scheme not in schemes:
                schemes.append(certificate.scheme)
        location = lot.site_id
        if lot_id in delivered:
            for shipment in dataset.shipments:
                if lot_id in shipment.lot_ids and shipment.to_site_id in retailer_sites:
                    location = shipment.to_site_id
        lots.append(
            LotView(
                lot_id=lot_id,
                site_id=location,
                quantity_kg=int(lot.quantity),
                delivered=lot_id in delivered,
                risk=float(economics["risk"]),
                value_eur_per_kg=float(economics["value_eur_per_kg"]),
                valid_schemes=tuple(schemes),
            )
        )
    return Problem(root_lot_id, lots, parameters, "baseline")


def replace_parameters(parameters: Parameters, **changes: Any) -> Parameters:
    return replace(parameters, **changes)
