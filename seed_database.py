#!/usr/bin/env python3
"""
seed_database.py
────────────────
Reads all generated CSVs from ./data/ and loads them into SQLite (./data/rms.db).

Usage:
    python seed_database.py                # load CSVs → SQLite
    python seed_database.py --clear        # drop all tables first, then load
    python seed_database.py --data-dir /path/to/data   # custom data dir

Load order respects FK dependencies:
  customers → inventory → orders → order_lines →
  return_requests → return_lines →
  return_authorizations → return_shipments →
  inspections → refunds → inventory_dispositions →
  state_transition_log → anomaly_records → company_financials
"""

import argparse
import os
import sys
import csv
import sqlite3
from pathlib import Path
from datetime import datetime

# ─────────────────────────────────────────────────────────────────────────────
# Table definitions (DDL)
# ─────────────────────────────────────────────────────────────────────────────

TABLES_DDL = {
    "customers": """
        CREATE TABLE IF NOT EXISTS customers (
            customer_id         TEXT PRIMARY KEY,
            name                TEXT NOT NULL,
            email               TEXT NOT NULL UNIQUE,
            phone               TEXT,
            address             TEXT,
            city                TEXT,
            state               TEXT,
            tier                TEXT NOT NULL CHECK(tier IN ('standard','premium','vip')),
            wallet_balance_inr  REAL DEFAULT 0.0,
            created_at          TEXT,
            is_active           INTEGER DEFAULT 1
        )
    """,
    "inventory": """
        CREATE TABLE IF NOT EXISTS inventory (
            product_id           TEXT PRIMARY KEY,
            product_name         TEXT NOT NULL,
            category             TEXT,
            unit_price_inr       REAL,
            cost_price_inr       REAL,
            stock_quantity       INTEGER,
            return_window_days   INTEGER DEFAULT 7,
            is_returnable        INTEGER DEFAULT 1,
            gst_pct              REAL DEFAULT 18.0,
            total_units_sold     INTEGER DEFAULT 0,
            total_units_returned INTEGER DEFAULT 0
        )
    """,
    "orders": """
        CREATE TABLE IF NOT EXISTS orders (
            order_id              TEXT PRIMARY KEY,
            customer_id           TEXT NOT NULL REFERENCES customers(customer_id),
            order_date            TEXT,
            total_amount_inr      REAL,
            discount_amount_inr   REAL DEFAULT 0,
            tax_amount_inr        REAL DEFAULT 0,
            net_amount_inr        REAL,
            status                TEXT,
            payment_method        TEXT,
            delivery_date         TEXT
        )
    """,
    "order_lines": """
        CREATE TABLE IF NOT EXISTS order_lines (
            line_id              TEXT PRIMARY KEY,
            order_id             TEXT NOT NULL REFERENCES orders(order_id),
            product_id           TEXT,
            product_name         TEXT,
            category             TEXT,
            quantity             INTEGER,
            unit_price_inr       REAL,
            discount_pct         REAL DEFAULT 0,
            gst_pct              REAL DEFAULT 18.0,
            line_total_inr       REAL,
            is_returnable        INTEGER DEFAULT 1,
            return_window_days   INTEGER DEFAULT 7
        )
    """,
    "return_requests": """
        CREATE TABLE IF NOT EXISTS return_requests (
            request_id           TEXT PRIMARY KEY,
            customer_id          TEXT NOT NULL REFERENCES customers(customer_id),
            order_id             TEXT NOT NULL REFERENCES orders(order_id),
            request_date         TEXT,
            reason               TEXT,
            status               TEXT,
            notes                TEXT,
            override_flag        INTEGER DEFAULT 0,
            override_reason      TEXT,
            days_since_delivery  INTEGER,
            return_channel       TEXT DEFAULT 'customer_portal'
        )
    """,
    "return_lines": """
        CREATE TABLE IF NOT EXISTS return_lines (
            line_id              TEXT PRIMARY KEY,
            request_id           TEXT NOT NULL REFERENCES return_requests(request_id),
            order_line_id        TEXT NOT NULL REFERENCES order_lines(line_id),
            requested_qty        INTEGER,
            approved_qty         INTEGER,
            rejection_reason     TEXT,
            status               TEXT
        )
    """,
    "return_authorizations": """
        CREATE TABLE IF NOT EXISTS return_authorizations (
            auth_id              TEXT PRIMARY KEY,
            request_id           TEXT NOT NULL UNIQUE REFERENCES return_requests(request_id),
            authorized_by        TEXT,
            authorized_at        TEXT,
            expiry_date          TEXT,
            auth_status          TEXT
        )
    """,
    "return_shipments": """
        CREATE TABLE IF NOT EXISTS return_shipments (
            shipment_id          TEXT PRIMARY KEY,
            auth_id              TEXT NOT NULL REFERENCES return_authorizations(auth_id),
            carrier              TEXT,
            tracking_number      TEXT,
            shipped_at           TEXT,
            received_at          TEXT,
            condition_on_arrival TEXT,
            status               TEXT
        )
    """,
    "inspections": """
        CREATE TABLE IF NOT EXISTS inspections (
            inspection_id        TEXT PRIMARY KEY,
            shipment_id          TEXT NOT NULL UNIQUE REFERENCES return_shipments(shipment_id),
            inspector_id         TEXT,
            inspected_at         TEXT,
            overall_condition    TEXT,
            notes                TEXT,
            recommended_action   TEXT
        )
    """,
    "refunds": """
        CREATE TABLE IF NOT EXISTS refunds (
            refund_id                TEXT PRIMARY KEY,
            request_id               TEXT NOT NULL REFERENCES return_requests(request_id),
            inspection_id            TEXT,
            gross_refund_inr         REAL DEFAULT 0,
            restocking_fee_inr       REAL DEFAULT 0,
            shipping_fee_inr         REAL DEFAULT 0,
            net_refund_inr           REAL DEFAULT 0,
            status                   TEXT,
            processed_at             TEXT,
            payment_method           TEXT,
            is_duplicate             INTEGER DEFAULT 0,
            duplicate_of_refund_id   TEXT
        )
    """,
    "inventory_dispositions": """
        CREATE TABLE IF NOT EXISTS inventory_dispositions (
            disposition_id           TEXT PRIMARY KEY,
            inspection_id            TEXT,
            product_id               TEXT,
            product_name             TEXT,
            quantity                 INTEGER,
            disposition_action       TEXT,
            location                 TEXT,
            disposed_at              TEXT,
            estimated_recovery_inr   REAL DEFAULT 0,
            notes                    TEXT
        )
    """,
    "state_transition_log": """
        CREATE TABLE IF NOT EXISTS state_transition_log (
            log_id               TEXT PRIMARY KEY,
            entity_type          TEXT,
            entity_id            TEXT,
            from_status          TEXT,
            to_status            TEXT,
            changed_by           TEXT,
            changed_at           TEXT,
            reason               TEXT
        )
    """,
    "anomaly_records": """
        CREATE TABLE IF NOT EXISTS anomaly_records (
            anomaly_id           TEXT PRIMARY KEY,
            entity_type          TEXT,
            entity_id            TEXT,
            anomaly_type         TEXT,
            severity             TEXT,
            description          TEXT,
            detected_at          TEXT,
            is_confirmed         INTEGER DEFAULT 1
        )
    """
}

# CSV → table mapping (in load order)
LOAD_ORDER = [
    ("customers.csv",              "customers"),
    ("inventory.csv",              "inventory"),
    ("orders.csv",                 "orders"),
    ("order_lines.csv",            "order_lines"),
    ("return_requests.csv",        "return_requests"),
    ("return_lines.csv",           "return_lines"),
    ("return_authorizations.csv",  "return_authorizations"),
    ("return_shipments.csv",       "return_shipments"),
    ("inspections.csv",            "inspections"),
    ("refunds.csv",                "refunds"),
    ("inventory_dispositions.csv", "inventory_dispositions"),
    ("state_transition_log.csv",   "state_transition_log"),
    ("ground_truth.csv",           "anomaly_records"),
]


def _coerce_row(row: dict) -> dict:
    out = {}
    for k, v in row.items():
        if v == "" or v is None:
            out[k] = None
        elif str(v).lower() == "true":
            out[k] = 1
        elif str(v).lower() == "false":
            out[k] = 0
        else:
            out[k] = v
    return out


def _bulk_insert(conn: sqlite3.Connection, table_name: str, rows: list[dict]) -> int:
    if not rows:
        return 0

    cursor = conn.cursor()
    cursor.execute(f"PRAGMA table_info({table_name})")
    table_cols = {col[1] for col in cursor.fetchall()}

    valid_cols = [c for c in rows[0].keys() if c in table_cols]
    if not valid_cols:
        return 0

    col_names = ", ".join(valid_cols)
    placeholders = ", ".join(["?"] * len(valid_cols))
    sql = f"INSERT OR REPLACE INTO {table_name} ({col_names}) VALUES ({placeholders})"

    data = [tuple(row.get(c) for c in valid_cols) for row in rows]
    conn.executemany(sql, data)
    conn.commit()
    return len(data)


def create_schema(conn: sqlite3.Connection):
    cursor = conn.cursor()
    cursor.execute("PRAGMA foreign_keys = OFF;")
    for table_name, ddl in TABLES_DDL.items():
        cursor.execute(ddl)
    conn.commit()
    cursor.execute("PRAGMA foreign_keys = ON;")


def drop_schema(conn: sqlite3.Connection):
    cursor = conn.cursor()
    cursor.execute("PRAGMA foreign_keys = OFF;")
    for table_name in reversed(list(TABLES_DDL.keys())):
        cursor.execute(f"DROP TABLE IF EXISTS {table_name};")
    conn.commit()
    cursor.execute("PRAGMA foreign_keys = ON;")


def seed_database(data_dir: str = "data", db_path: str = "data/rms.db", clear: bool = False):
    print("=" * 60)
    print("  RMS Database Seeder")
    print(f"  DB:   {os.path.abspath(db_path)}")
    print(f"  Data: {os.path.abspath(data_dir)}")
    print(f"  Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 60)

    os.makedirs(os.path.dirname(os.path.abspath(db_path)), exist_ok=True)
    conn = sqlite3.connect(db_path)

    if clear:
        print("\n→ --clear flag: dropping all tables...")
        drop_schema(conn)
        print("  ✓ All tables dropped.")

    print("→ Creating tables (if not exist)...")
    create_schema(conn)
    print("  ✓ All tables created.")

    summary = {}
    for csv_file, table_name in LOAD_ORDER:
        file_path = os.path.join(data_dir, csv_file)
        if not os.path.exists(file_path):
            print(f"  ⚠ Skipping {csv_file} (file not found)")
            continue

        with open(file_path, "r", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            rows = [_coerce_row(r) for r in reader]

        inserted = _bulk_insert(conn, table_name, rows)
        summary[table_name] = inserted
        print(f"  ✓ {csv_file:<26} → {table_name:<24} ({inserted:>6} rows)")

    print("\n" + "=" * 60)
    print("  SEEDING COMPLETE")
    print("=" * 60)
    for tbl, cnt in summary.items():
        print(f"  {tbl:<28}: {cnt:>7} records")

    conn.close()


def main():
    parser = argparse.ArgumentParser(description="Seed SQLite RMS database from CSVs")
    parser.add_argument("--data-dir", default="data", help="Directory containing CSV files")
    parser.add_argument("--db-path", default="data/rms.db", help="Path to SQLite database")
    parser.add_argument("--clear", action="store_true", help="Drop all tables before loading")
    args = parser.parse_args()

    seed_database(data_dir=args.data_dir, db_path=args.db_path, clear=args.clear)


if __name__ == "__main__":
    main()
