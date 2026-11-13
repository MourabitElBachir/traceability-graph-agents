"""SQLite ERP extract and the round trip back into domain records."""

from __future__ import annotations

import json
import sqlite3
from importlib.resources import files
from pathlib import Path

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


def schema_sql() -> str:
    return files("agritrace.data").joinpath("schema.sql").read_text(encoding="utf-8")


def _json(values: list[str]) -> str:
    return json.dumps(values, ensure_ascii=False)


def write_dataset(conn: sqlite3.Connection, dataset: Dataset) -> None:
    conn.executescript(schema_sql())
    conn.executemany(
        "INSERT INTO actors (id, name, role) VALUES (?, ?, ?)",
        [(row.id, row.name, row.role) for row in dataset.actors],
    )
    conn.executemany(
        "INSERT INTO sites (id, name, actor_id, country, gln) VALUES (?, ?, ?, ?, ?)",
        [(row.id, row.name, row.actor_id, row.country, row.gln) for row in dataset.sites],
    )
    conn.executemany(
        "INSERT INTO products (id, name, gtin, category) VALUES (?, ?, ?, ?)",
        [(row.id, row.name, row.gtin, row.category) for row in dataset.products],
    )
    conn.executemany(
        """
        INSERT INTO ingredients (id, name, product_id, parent_product_id)
        VALUES (?, ?, ?, ?)
        """,
        [(row.id, row.name, row.product_id, row.parent_product_id) for row in dataset.ingredients],
    )
    conn.executemany(
        """
        INSERT INTO lots
            (id, lot_code, product_id, quantity, unit, produced_on, site_id, claimed_schemes)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """,
        [
            (
                row.id,
                row.lot_code,
                row.product_id,
                row.quantity,
                row.unit,
                row.produced_on,
                row.site_id,
                _json(row.claimed_schemes),
            )
            for row in dataset.lots
        ],
    )
    conn.executemany(
        """
        INSERT INTO process_steps (id, biz_step, event_time, site_id, ingredient_ids)
        VALUES (?, ?, ?, ?, ?)
        """,
        [(row.id, row.biz_step, row.event_time, row.site_id, _json(row.ingredient_ids)) for row in dataset.processes],
    )
    conn.executemany(
        "INSERT INTO process_inputs (step_id, lot_id, quantity, unit) VALUES (?, ?, ?, ?)",
        [(step.id, link.lot_id, link.quantity, link.unit) for step in dataset.processes for link in step.inputs],
    )
    conn.executemany(
        "INSERT INTO process_outputs (step_id, lot_id, quantity, unit) VALUES (?, ?, ?, ?)",
        [(step.id, link.lot_id, link.quantity, link.unit) for step in dataset.processes for link in step.outputs],
    )
    conn.executemany(
        """
        INSERT INTO shipments (id, shipped_on, from_site_id, to_site_id, sscc)
        VALUES (?, ?, ?, ?, ?)
        """,
        [(row.id, row.shipped_on, row.from_site_id, row.to_site_id, row.sscc) for row in dataset.shipments],
    )
    conn.executemany(
        "INSERT INTO shipment_lines (shipment_id, lot_id) VALUES (?, ?)",
        [(row.id, lot_id) for row in dataset.shipments for lot_id in row.lot_ids],
    )
    conn.executemany(
        """
        INSERT INTO certificates (
            id, scheme, status, valid_from, valid_to, issuer_actor_id, holder_actor_id,
            covers_lot_ids, covers_site_ids, covers_actor_ids
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
        [
            (
                row.id,
                row.scheme,
                row.status,
                row.valid_from,
                row.valid_to,
                row.issuer_actor_id,
                row.holder_actor_id,
                _json(row.covers_lot_ids),
                _json(row.covers_site_ids),
                _json(row.covers_actor_ids),
            )
            for row in dataset.certificates
        ],
    )
    conn.executemany(
        """
        INSERT INTO audits (
            id, audit_date, result, site_id, auditor_actor_id, certificate_id, summary
        ) VALUES (?, ?, ?, ?, ?, ?, ?)
        """,
        [
            (
                row.id,
                row.audit_date,
                row.result,
                row.site_id,
                row.auditor_actor_id,
                row.certificate_id,
                row.summary,
            )
            for row in dataset.audits
        ],
    )
    conn.executemany(
        "INSERT INTO documents (id, title, kind, body, about_ids) VALUES (?, ?, ?, ?, ?)",
        [(row.id, row.title, row.kind, row.text, _json(row.about_ids)) for row in dataset.documents],
    )
    conn.commit()


def read_dataset(conn: sqlite3.Connection) -> Dataset:
    conn.row_factory = sqlite3.Row

    def loads(value: str) -> list[str]:
        parsed: list[str] = json.loads(value)
        return parsed

    inputs: dict[str, list[LotQuantity]] = {}
    outputs: dict[str, list[LotQuantity]] = {}
    for row in conn.execute("SELECT step_id, lot_id, quantity, unit FROM process_inputs ORDER BY step_id, lot_id"):
        inputs.setdefault(str(row["step_id"]), []).append(
            LotQuantity(lot_id=str(row["lot_id"]), quantity=float(row["quantity"]), unit=str(row["unit"]))
        )
    for row in conn.execute("SELECT step_id, lot_id, quantity, unit FROM process_outputs ORDER BY step_id, lot_id"):
        outputs.setdefault(str(row["step_id"]), []).append(
            LotQuantity(lot_id=str(row["lot_id"]), quantity=float(row["quantity"]), unit=str(row["unit"]))
        )
    lines: dict[str, list[str]] = {}
    for row in conn.execute("SELECT shipment_id, lot_id FROM shipment_lines ORDER BY lot_id"):
        lines.setdefault(str(row["shipment_id"]), []).append(str(row["lot_id"]))

    return Dataset(
        actors=[
            Actor(id=row["id"], name=row["name"], role=row["role"])
            for row in conn.execute("SELECT * FROM actors ORDER BY id")
        ],
        sites=[
            Site(id=row["id"], name=row["name"], actor_id=row["actor_id"], country=row["country"], gln=row["gln"])
            for row in conn.execute("SELECT * FROM sites ORDER BY id")
        ],
        products=[
            Product(id=row["id"], name=row["name"], gtin=row["gtin"], category=row["category"])
            for row in conn.execute("SELECT * FROM products ORDER BY id")
        ],
        ingredients=[
            Ingredient(
                id=row["id"],
                name=row["name"],
                product_id=row["product_id"],
                parent_product_id=row["parent_product_id"],
            )
            for row in conn.execute("SELECT * FROM ingredients ORDER BY id")
        ],
        lots=[
            Lot(
                id=row["id"],
                lot_code=row["lot_code"],
                product_id=row["product_id"],
                quantity=float(row["quantity"]),
                unit=row["unit"],
                produced_on=row["produced_on"],
                site_id=row["site_id"],
                claimed_schemes=loads(row["claimed_schemes"]),
            )
            for row in conn.execute("SELECT * FROM lots ORDER BY id")
        ],
        processes=[
            ProcessStep(
                id=row["id"],
                biz_step=row["biz_step"],
                event_time=row["event_time"],
                site_id=row["site_id"],
                inputs=inputs.get(str(row["id"]), []),
                outputs=outputs.get(str(row["id"]), []),
                ingredient_ids=loads(row["ingredient_ids"]),
            )
            for row in conn.execute("SELECT * FROM process_steps ORDER BY id")
        ],
        shipments=[
            Shipment(
                id=row["id"],
                shipped_on=row["shipped_on"],
                from_site_id=row["from_site_id"],
                to_site_id=row["to_site_id"],
                lot_ids=lines.get(str(row["id"]), []),
                sscc=row["sscc"],
            )
            for row in conn.execute("SELECT * FROM shipments ORDER BY id")
        ],
        certificates=[
            Certificate(
                id=row["id"],
                scheme=row["scheme"],
                status=row["status"],
                valid_from=row["valid_from"],
                valid_to=row["valid_to"],
                issuer_actor_id=row["issuer_actor_id"],
                holder_actor_id=row["holder_actor_id"],
                covers_lot_ids=loads(row["covers_lot_ids"]),
                covers_site_ids=loads(row["covers_site_ids"]),
                covers_actor_ids=loads(row["covers_actor_ids"]),
            )
            for row in conn.execute("SELECT * FROM certificates ORDER BY id")
        ],
        audits=[
            Audit(
                id=row["id"],
                audit_date=row["audit_date"],
                result=row["result"],
                site_id=row["site_id"],
                auditor_actor_id=row["auditor_actor_id"],
                certificate_id=row["certificate_id"],
                summary=row["summary"],
            )
            for row in conn.execute("SELECT * FROM audits ORDER BY id")
        ],
        documents=[
            Document(
                id=row["id"],
                title=row["title"],
                kind=row["kind"],
                text=row["body"],
                about_ids=loads(row["about_ids"]),
            )
            for row in conn.execute("SELECT * FROM documents ORDER BY id")
        ],
    )


def roundtrip(dataset: Dataset, path: str | Path = ":memory:") -> Dataset:
    """Write the extract and read it back. This is the SQL side of ingestion."""

    conn = sqlite3.connect(str(path))
    try:
        write_dataset(conn, dataset)
        return read_dataset(conn)
    finally:
        conn.close()
