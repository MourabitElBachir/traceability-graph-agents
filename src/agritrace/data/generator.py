"""Deterministic fictional agrifood chains.

The running example, used by the README, the tests, and the docs, is:

    wheat BLE-0457  ->  flour FAR-118  ->  biscuits BIS-031

covered by certificate CERT-77. Other lots exist only to show an expired
certificate, a mixed lot, and a broken chain. No real company is named.
"""

from __future__ import annotations

from agritrace.models import (
    Actor,
    Audit,
    Certificate,
    Dataset,
    Document,
    Ingredient,
    Lot,
    LotQuantity,
    ProcessStep,
    Product,
    Shipment,
    Site,
)

ONTOLOGY_VERSION = "0.1.0"
HERO_WHEAT = "BLE-0457"
HERO_FLOUR = "FAR-118"
HERO_BISCUITS = "BIS-031"
HERO_CERT = "CERT-77"


def build_dataset() -> Dataset:
    actors = [
        Actor(id="ACT-COLLINES", name="Ferme des Collines", role="farm"),
        Actor(id="ACT-BRUME", name="Ferme Brume", role="farm"),
        Actor(id="ACT-SAULES", name="Ferme des Saules", role="farm"),
        Actor(id="ACT-VAL", name="Moulin du Val", role="mill"),
        Actor(id="ACT-LUMIERE", name="Fournil Lumière", role="plant"),
        Actor(id="ACT-PRESS", name="Pressoir des Olivettes", role="plant"),
        Actor(id="ACT-DISTNORD", name="DistriNord Logistique", role="distributor"),
        Actor(id="ACT-RIVE", name="Épicerie Rive", role="retailer"),
        Actor(id="ACT-HALLE", name="Halle du Marché", role="retailer"),
        Actor(id="ACT-HORIZON", name="Organisme Horizon", role="certifier"),
        Actor(id="ACT-AUDIT", name="Atelier Audit Nord", role="auditor"),
    ]
    sites = [
        Site(id="SITE-COLLINES", name="Les Collines", actor_id="ACT-COLLINES", country="FR", gln="DEMO-GLN-COLLINES"),
        Site(id="SITE-BRUME", name="Plaine Brume", actor_id="ACT-BRUME", country="FR", gln="DEMO-GLN-BRUME"),
        Site(id="SITE-SAULES", name="Les Saules", actor_id="ACT-SAULES", country="FR", gln="DEMO-GLN-SAULES"),
        Site(id="SITE-VAL", name="Moulin du Val", actor_id="ACT-VAL", country="FR", gln="DEMO-GLN-VAL"),
        Site(id="SITE-LUMIERE", name="Fournil Lumière", actor_id="ACT-LUMIERE", country="FR", gln="DEMO-GLN-LUMIERE"),
        Site(id="SITE-PRESS", name="Pressoir des Olivettes", actor_id="ACT-PRESS", country="FR", gln="DEMO-GLN-PRESS"),
        Site(id="SITE-DISTNORD", name="Entrepôt Nord", actor_id="ACT-DISTNORD", country="FR", gln="DEMO-GLN-DISTNORD"),
        Site(id="SITE-RIVE", name="Épicerie Rive", actor_id="ACT-RIVE", country="FR", gln="DEMO-GLN-RIVE"),
        Site(id="SITE-HALLE", name="Halle du Marché", actor_id="ACT-HALLE", country="FR", gln="DEMO-GLN-HALLE"),
        Site(id="SITE-HORIZON", name="Bureau Horizon", actor_id="ACT-HORIZON", country="FR", gln="DEMO-GLN-HORIZON"),
    ]
    products = [
        Product(id="PRD-WHEAT", name="Blé tendre", gtin="DEMO-GTIN-WHEAT", category="grain"),
        Product(id="PRD-FLOUR", name="Farine de blé T65", gtin="DEMO-GTIN-FLOUR", category="flour"),
        Product(id="PRD-BISCUIT", name="Biscuits sablés", gtin="DEMO-GTIN-BISCUIT", category="bakery"),
        Product(id="PRD-OLIVE", name="Olives", gtin="DEMO-GTIN-OLIVE", category="fruit"),
        Product(id="PRD-OIL", name="Huile d'olive", gtin="DEMO-GTIN-OIL", category="oil"),
    ]
    ingredients = [
        Ingredient(id="ING-WHEAT", name="Blé", product_id="PRD-WHEAT", parent_product_id="PRD-FLOUR"),
        Ingredient(id="ING-FLOUR", name="Farine", product_id="PRD-FLOUR", parent_product_id="PRD-BISCUIT"),
        Ingredient(id="ING-OLIVE", name="Olives", product_id="PRD-OLIVE", parent_product_id="PRD-OIL"),
    ]
    lots = [
        Lot(
            id=HERO_WHEAT,
            lot_code="BLE-0457",
            product_id="PRD-WHEAT",
            quantity=12000,
            unit="kg",
            produced_on="2026-06-12",
            site_id="SITE-COLLINES",
            claimed_schemes=["Organic Horizon"],
        ),
        Lot(
            id=HERO_FLOUR,
            lot_code="FAR-118",
            product_id="PRD-FLOUR",
            quantity=9400,
            unit="kg",
            produced_on="2026-07-03",
            site_id="SITE-VAL",
            claimed_schemes=["Organic Horizon"],
        ),
        Lot(
            id=HERO_BISCUITS,
            lot_code="BIS-031",
            product_id="PRD-BISCUIT",
            quantity=7100,
            unit="kg",
            produced_on="2026-07-22",
            site_id="SITE-LUMIERE",
            claimed_schemes=["Organic Horizon"],
        ),
        Lot(
            id="BLE-0881",
            lot_code="BLE-0881",
            product_id="PRD-WHEAT",
            quantity=4000,
            unit="kg",
            produced_on="2026-06-18",
            site_id="SITE-BRUME",
            claimed_schemes=["Organic Horizon"],
        ),
        Lot(
            id="BLE-0902",
            lot_code="BLE-0902",
            product_id="PRD-WHEAT",
            quantity=4000,
            unit="kg",
            produced_on="2026-06-20",
            site_id="SITE-SAULES",
            claimed_schemes=["Organic Horizon"],
        ),
        Lot(
            id="FAR-221",
            lot_code="FAR-221",
            product_id="PRD-FLOUR",
            quantity=6200,
            unit="kg",
            produced_on="2026-07-08",
            site_id="SITE-VAL",
            claimed_schemes=["Organic Horizon"],
        ),
        Lot(
            id="OIL-009",
            lot_code="OIL-009",
            product_id="PRD-OIL",
            quantity=500,
            unit="L",
            produced_on="2026-08-01",
            site_id="SITE-PRESS",
            claimed_schemes=[],
        ),
    ]
    processes = [
        ProcessStep(
            id="P-COMM-0457",
            biz_step="commissioning",
            event_time="2026-06-12T08:00:00+00:00",
            site_id="SITE-COLLINES",
            outputs=[LotQuantity(lot_id=HERO_WHEAT, quantity=12000)],
        ),
        ProcessStep(
            id="P-MILL-118",
            biz_step="transformation",
            event_time="2026-07-03T09:30:00+00:00",
            site_id="SITE-VAL",
            inputs=[LotQuantity(lot_id=HERO_WHEAT, quantity=12000)],
            outputs=[LotQuantity(lot_id=HERO_FLOUR, quantity=9400)],
            ingredient_ids=["ING-WHEAT"],
        ),
        ProcessStep(
            id="P-BAKE-031",
            biz_step="transformation",
            event_time="2026-07-22T06:15:00+00:00",
            site_id="SITE-LUMIERE",
            inputs=[LotQuantity(lot_id=HERO_FLOUR, quantity=9400)],
            outputs=[LotQuantity(lot_id=HERO_BISCUITS, quantity=7100)],
            ingredient_ids=["ING-FLOUR"],
        ),
        ProcessStep(
            id="P-COMM-0881",
            biz_step="commissioning",
            event_time="2026-06-18T08:00:00+00:00",
            site_id="SITE-BRUME",
            outputs=[LotQuantity(lot_id="BLE-0881", quantity=4000)],
        ),
        ProcessStep(
            id="P-COMM-0902",
            biz_step="commissioning",
            event_time="2026-06-20T08:00:00+00:00",
            site_id="SITE-SAULES",
            outputs=[LotQuantity(lot_id="BLE-0902", quantity=4000)],
        ),
        ProcessStep(
            id="P-MIX-221",
            biz_step="transformation",
            event_time="2026-07-08T11:00:00+00:00",
            site_id="SITE-VAL",
            inputs=[
                LotQuantity(lot_id="BLE-0881", quantity=4000),
                LotQuantity(lot_id="BLE-0902", quantity=4000),
            ],
            outputs=[LotQuantity(lot_id="FAR-221", quantity=6200)],
            ingredient_ids=["ING-WHEAT"],
        ),
        ProcessStep(
            id="P-PRESS-009",
            biz_step="transformation",
            event_time="2026-08-01T14:00:00+00:00",
            site_id="SITE-PRESS",
            inputs=[],
            outputs=[LotQuantity(lot_id="OIL-009", quantity=500, unit="L")],
            ingredient_ids=["ING-OLIVE"],
        ),
    ]
    shipments = [
        Shipment(
            id="SHIP-BIS-1",
            shipped_on="2026-07-23",
            from_site_id="SITE-LUMIERE",
            to_site_id="SITE-DISTNORD",
            lot_ids=[HERO_BISCUITS],
            sscc="DEMO-SSCC-BIS-1",
        ),
        Shipment(
            id="SHIP-BIS-2",
            shipped_on="2026-07-24",
            from_site_id="SITE-DISTNORD",
            to_site_id="SITE-RIVE",
            lot_ids=[HERO_BISCUITS],
            sscc="DEMO-SSCC-BIS-2",
        ),
        Shipment(
            id="SHIP-MIX-1",
            shipped_on="2026-07-09",
            from_site_id="SITE-VAL",
            to_site_id="SITE-HALLE",
            lot_ids=["FAR-221"],
            sscc="DEMO-SSCC-MIX-1",
        ),
        Shipment(
            id="SHIP-OIL-1",
            shipped_on="2026-08-02",
            from_site_id="SITE-PRESS",
            to_site_id="SITE-HALLE",
            lot_ids=["OIL-009"],
            sscc="DEMO-SSCC-OIL-1",
        ),
    ]
    certificates = [
        Certificate(
            id=HERO_CERT,
            scheme="Organic Horizon",
            status="valid",
            valid_from="2025-04-01",
            valid_to="2027-12-31",
            issuer_actor_id="ACT-HORIZON",
            holder_actor_id="ACT-LUMIERE",
            covers_lot_ids=[HERO_WHEAT, HERO_FLOUR, HERO_BISCUITS],
            covers_site_ids=["SITE-COLLINES", "SITE-VAL", "SITE-LUMIERE"],
            covers_actor_ids=["ACT-COLLINES", "ACT-VAL", "ACT-LUMIERE"],
        ),
        Certificate(
            id="CERT-78",
            scheme="Organic Horizon",
            status="expired",
            valid_from="2024-01-01",
            valid_to="2026-03-01",
            issuer_actor_id="ACT-HORIZON",
            holder_actor_id="ACT-BRUME",
            covers_lot_ids=["BLE-0881"],
            covers_site_ids=["SITE-BRUME"],
            covers_actor_ids=["ACT-BRUME"],
        ),
        Certificate(
            id="CERT-79",
            scheme="Organic Horizon",
            status="valid",
            valid_from="2025-06-01",
            valid_to="2027-06-01",
            issuer_actor_id="ACT-HORIZON",
            holder_actor_id="ACT-SAULES",
            covers_lot_ids=["BLE-0902"],
            covers_site_ids=["SITE-SAULES"],
            covers_actor_ids=["ACT-SAULES"],
        ),
    ]
    audits = [
        Audit(
            id="AUD-BAKE-2026",
            audit_date="2026-08-01",
            result="conform",
            site_id="SITE-LUMIERE",
            auditor_actor_id="ACT-AUDIT",
            certificate_id=HERO_CERT,
            summary=(
                "Fournil Lumière: biscuit lot BIS-031 is milled from FAR-118 and "
                "wheat BLE-0457. CERT-77 was in date. Result conform."
            ),
        ),
        Audit(
            id="AUD-MILL-2026",
            audit_date="2026-09-12",
            result="major_nonconformity",
            site_id="SITE-VAL",
            auditor_actor_id="ACT-AUDIT",
            certificate_id="CERT-78",
            summary=(
                "Moulin du Val mixed BLE-0881 (expired CERT-78) with BLE-0902 "
                "into flour FAR-221. Result major_nonconformity."
            ),
        ),
    ]
    documents = [
        Document(
            id="DOC-CERT-77",
            title="Organic Horizon certificate CERT-77",
            kind="certificate",
            about_ids=[HERO_CERT, HERO_WHEAT, HERO_FLOUR, HERO_BISCUITS, "ACT-LUMIERE"],
            text=(
                "Certificate CERT-77. Scheme: Organic Horizon (fictional). "
                "Issuer: Organisme Horizon. Holder: Fournil Lumière. "
                "Status: valid. Validity: 2025-04-01 to 2027-12-31. "
                "Scope of the batch genealogy: wheat lot BLE-0457 harvested at "
                "Ferme des Collines, milled as flour FAR-118 at Moulin du Val, "
                "baked as biscuits BIS-031 at Fournil Lumière. "
                "The scope is only this wheat, flour, and biscuit genealogy."
            ),
        ),
        Document(
            id="DOC-CERT-78",
            title="Expired certificate CERT-78",
            kind="certificate",
            about_ids=["CERT-78", "BLE-0881", "ACT-BRUME"],
            text=(
                "Certificate CERT-78. Scheme: Organic Horizon (fictional). "
                "Holder: Ferme Brume. Lot in scope: BLE-0881. "
                "Validity ended on 2026-03-01. Status: expired. "
                "The holder did not present a renewal before the mill audit."
            ),
        ),
        Document(
            id="DOC-AUDIT-MILL",
            title="Mill audit AUD-MILL-2026",
            kind="audit",
            about_ids=["AUD-MILL-2026", "FAR-221", "BLE-0881", "BLE-0902", "CERT-78", "SITE-VAL"],
            text=(
                "Mill audit AUD-MILL-2026 of Moulin du Val (SITE-VAL), 2026-09-12. "
                "Auditor: Atelier Audit Nord. Result: major_nonconformity. "
                "Finding: process P-MIX-221 mixed wheat BLE-0881, covered only by "
                "expired certificate CERT-78, with wheat BLE-0902. "
                "Output lot FAR-221 keeps an organic claim. Quarantine FAR-221 "
                "at Halle du Marché. The biscuit line was out of scope for this finding."
            ),
        ),
        Document(
            id="DOC-RECALL-PLAYBOOK",
            title="Recall playbook",
            kind="procedure",
            about_ids=["ACT-HORIZON"],
            text=(
                "Recall playbook. A recall recommendation lists downstream lots, "
                "shipments, and retail sites. A person must approve it before it "
                "is issued. The assistant never issues a recall on its own."
            ),
        ),
    ]
    return Dataset(
        actors=actors,
        sites=sites,
        products=products,
        ingredients=ingredients,
        lots=lots,
        processes=processes,
        shipments=shipments,
        certificates=certificates,
        audits=audits,
        documents=documents,
    )
