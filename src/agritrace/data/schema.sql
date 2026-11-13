-- ERP extract. SQLite is the local system of record.
-- The same column names are valid in Postgres (TEXT, REAL, and JSON stored as TEXT).

PRAGMA foreign_keys = ON;

CREATE TABLE actors (
    id TEXT PRIMARY KEY,
    name TEXT NOT NULL,
    role TEXT NOT NULL
);

CREATE TABLE sites (
    id TEXT PRIMARY KEY,
    name TEXT NOT NULL,
    actor_id TEXT NOT NULL REFERENCES actors(id),
    country TEXT NOT NULL,
    gln TEXT NOT NULL
);

CREATE TABLE products (
    id TEXT PRIMARY KEY,
    name TEXT NOT NULL,
    gtin TEXT NOT NULL,
    category TEXT NOT NULL
);

CREATE TABLE ingredients (
    id TEXT PRIMARY KEY,
    name TEXT NOT NULL,
    product_id TEXT NOT NULL REFERENCES products(id),
    parent_product_id TEXT NOT NULL REFERENCES products(id)
);

CREATE TABLE lots (
    id TEXT PRIMARY KEY,
    lot_code TEXT NOT NULL,
    product_id TEXT NOT NULL REFERENCES products(id),
    quantity REAL NOT NULL,
    unit TEXT NOT NULL,
    produced_on TEXT NOT NULL,
    site_id TEXT NOT NULL REFERENCES sites(id),
    claimed_schemes TEXT NOT NULL
);

CREATE TABLE process_steps (
    id TEXT PRIMARY KEY,
    biz_step TEXT NOT NULL,
    event_time TEXT NOT NULL,
    site_id TEXT NOT NULL REFERENCES sites(id),
    ingredient_ids TEXT NOT NULL
);

CREATE TABLE process_inputs (
    step_id TEXT NOT NULL REFERENCES process_steps(id),
    lot_id TEXT NOT NULL REFERENCES lots(id),
    quantity REAL NOT NULL,
    unit TEXT NOT NULL,
    PRIMARY KEY (step_id, lot_id)
);

CREATE TABLE process_outputs (
    step_id TEXT NOT NULL REFERENCES process_steps(id),
    lot_id TEXT NOT NULL REFERENCES lots(id),
    quantity REAL NOT NULL,
    unit TEXT NOT NULL,
    PRIMARY KEY (step_id, lot_id)
);

CREATE TABLE shipments (
    id TEXT PRIMARY KEY,
    shipped_on TEXT NOT NULL,
    from_site_id TEXT NOT NULL REFERENCES sites(id),
    to_site_id TEXT NOT NULL REFERENCES sites(id),
    sscc TEXT NOT NULL
);

CREATE TABLE shipment_lines (
    shipment_id TEXT NOT NULL REFERENCES shipments(id),
    lot_id TEXT NOT NULL REFERENCES lots(id),
    PRIMARY KEY (shipment_id, lot_id)
);

CREATE TABLE certificates (
    id TEXT PRIMARY KEY,
    scheme TEXT NOT NULL,
    status TEXT NOT NULL,
    valid_from TEXT NOT NULL,
    valid_to TEXT NOT NULL,
    issuer_actor_id TEXT NOT NULL REFERENCES actors(id),
    holder_actor_id TEXT NOT NULL REFERENCES actors(id),
    covers_lot_ids TEXT NOT NULL,
    covers_site_ids TEXT NOT NULL,
    covers_actor_ids TEXT NOT NULL
);

CREATE TABLE audits (
    id TEXT PRIMARY KEY,
    audit_date TEXT NOT NULL,
    result TEXT NOT NULL,
    site_id TEXT NOT NULL REFERENCES sites(id),
    auditor_actor_id TEXT NOT NULL REFERENCES actors(id),
    certificate_id TEXT REFERENCES certificates(id),
    summary TEXT NOT NULL
);

CREATE TABLE documents (
    id TEXT PRIMARY KEY,
    title TEXT NOT NULL,
    kind TEXT NOT NULL,
    body TEXT NOT NULL,
    about_ids TEXT NOT NULL
);

CREATE INDEX idx_lots_site ON lots(site_id);
CREATE INDEX idx_process_inputs_lot ON process_inputs(lot_id);
CREATE INDEX idx_shipment_lines_lot ON shipment_lines(lot_id);
CREATE INDEX idx_certificates_valid_to ON certificates(valid_to);
