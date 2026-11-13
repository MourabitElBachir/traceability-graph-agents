"""The running example is wheat BLE-0457 -> flour FAR-118 -> biscuits BIS-031 under CERT-77."""

from __future__ import annotations

import pytest

from agritrace.data.erp import roundtrip
from agritrace.data.generator import HERO_BISCUITS, HERO_CERT, HERO_FLOUR, HERO_WHEAT, build_dataset
from agritrace.data.quality import check_quality
from agritrace.eval.runner import run
from agritrace.ontology.loader import summarise
from agritrace.security.cypher_guard import CypherRejected, validate_cypher
from agritrace.service import TraceService


def test_ontology_lists_the_vocabulary() -> None:
    summary = summarise()
    assert summary["version"] == "0.1.0"
    labels = " ".join(str(item) for item in summary["classes"])
    for name in ("Actor", "Lot", "Process step", "Certificate", "Shipment"):
        assert name in labels


def test_seed_contains_the_hero_ids() -> None:
    dataset = build_dataset()
    lot_ids = {lot.id for lot in dataset.lots}
    assert {HERO_WHEAT, HERO_FLOUR, HERO_BISCUITS} <= lot_ids
    assert HERO_CERT in {row.id for row in dataset.certificates}
    report = check_quality(dataset)
    assert report.ok
    assert "expired_certificate:CERT-78" in report.findings
    assert any(item.startswith("broken_chain:") for item in report.findings)


def test_quality_rejects_a_dangling_lot() -> None:
    dataset = build_dataset()
    dataset.lots[0].product_id = "missing-product"
    assert not check_quality(dataset).ok


def test_sql_roundtrip_keeps_the_hero_chain() -> None:
    loaded = roundtrip(build_dataset())
    lots = {lot.id: lot for lot in loaded.lots}
    assert lots[HERO_WHEAT].site_id == "SITE-COLLINES"
    assert lots[HERO_FLOUR].product_id == "PRD-FLOUR"
    assert lots[HERO_BISCUITS].claimed_schemes == ["Organic Horizon"]
    cert = next(row for row in loaded.certificates if row.id == HERO_CERT)
    assert cert.covers_lot_ids == [HERO_WHEAT, HERO_FLOUR, HERO_BISCUITS]


def test_upstream_and_downstream(engine: TraceService) -> None:
    upstream = engine.trace(HERO_BISCUITS, "upstream")
    assert upstream["path_lot_ids"] == [HERO_WHEAT, HERO_FLOUR, HERO_BISCUITS]
    assert upstream["origin_actor_name"] == "Ferme des Collines"
    assert HERO_CERT in upstream["certificate_ids"]
    assert "BLE-0881" not in upstream["lot_ids"]
    downstream = engine.trace(HERO_WHEAT, "downstream")
    assert downstream["downstream_lot_ids"] == [HERO_FLOUR, HERO_BISCUITS]
    assert any("Épicerie Rive" in site for site in downstream["retail_sites"])


def test_biscuits_are_compliant_and_mix_and_oil_are_not(engine: TraceService) -> None:
    biscuits = engine.check(HERO_BISCUITS)
    assert biscuits["compliant"] is True
    assert biscuits["certificate_ids"] == [HERO_CERT]
    mixed = engine.check("FAR-221")
    assert mixed["compliant"] is False
    assert {flag["code"] for flag in mixed["flags"]} >= {"mixed_lots", "expired_certificate"}
    oil = engine.check("OIL-009")
    assert any(flag["code"] == "broken_chain" for flag in oil["flags"])


def test_cypher_guard_and_hero_query(engine: TraceService) -> None:
    with pytest.raises(CypherRejected):
        validate_cypher("MATCH (n:Lot) DETACH DELETE n RETURN n LIMIT 5")
    safe = validate_cypher(
        "MATCH (wheat:Lot {id: 'BLE-0457'})-[:INPUT_OF]->(flour:Lot {id: 'FAR-118'})"
        "-[:INPUT_OF]->(biscuits:Lot {id: 'BIS-031'}) "
        "MATCH (cert:Certificate {id: 'CERT-77'})-[:COVERS]->(biscuits) "
        "RETURN wheat.id AS wheat, flour.id AS flour, biscuits.id AS biscuits, cert.id AS certificate "
        "LIMIT 5"
    )
    rows = engine.store.run_read_cypher(safe, {})
    assert rows[0]["certificate"] == "CERT-77"


def test_eval_suite(engine: TraceService) -> None:
    rows = run(engine)
    failed = [row for row in rows if not row["ok"]]
    assert failed == []
