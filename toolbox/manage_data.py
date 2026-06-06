#!/usr/bin/env python3
"""
db_tool.py — Export or import all data from rhum_recipes.db.

EXPORT
    python db_tool.py export                          # writes to ./export/
    python db_tool.py export --out ./backup           # custom output folder
    python db_tool.py export --db /path/to/db         # custom db path

IMPORT
    python db_tool.py import                          # reads ./export/full_export.json
    python db_tool.py import --src ./backup           # per-table JSONs or full_export.json
    python db_tool.py import --src ./backup/full_export.json
    python db_tool.py import --truncate               # wipe tables before inserting
"""

import argparse
import json
import sqlite3
from datetime import date, datetime
from pathlib import Path


# Insert / export order: parents before children (FK constraints)
TABLES = [
    "users",
    "global_ingredients",
    "recipes",
    "recipe_ingredients",
    "stock_entries",
    "clients",
    "bottle_orders",
]


# ---------------------------------------------------------------------------
# Shared helpers
# ---------------------------------------------------------------------------

def connect(db_path: Path) -> sqlite3.Connection:
    if not db_path.exists():
        print(f"❌  Database not found: {db_path}")
        raise SystemExit(1)
    conn = sqlite3.connect(db_path)
    conn.execute("PRAGMA foreign_keys = ON")
    return conn


def json_serializer(obj):
    if isinstance(obj, (datetime, date)):
        return obj.isoformat()
    raise TypeError(f"Type {type(obj)} not serializable")


# ---------------------------------------------------------------------------
# Export
# ---------------------------------------------------------------------------

def export_table(conn: sqlite3.Connection, table: str) -> list[dict]:
    conn.row_factory = sqlite3.Row
    cursor = conn.execute(f"SELECT * FROM {table}")  # noqa: S608
    return [dict(row) for row in cursor.fetchall()]


def cmd_export(args):
    out_dir = Path(args.out)
    out_dir.mkdir(parents=True, exist_ok=True)
    conn = connect(Path(args.db))

    full_export = {}
    total = 0

    for table in TABLES:
        try:
            rows = export_table(conn, table)
        except sqlite3.OperationalError as e:
            print(f"⚠️   Skipping '{table}': {e}")
            continue

        full_export[table] = rows
        total += len(rows)

        out_file = out_dir / f"{table}.json"
        out_file.write_text(json.dumps(rows, indent=2, default=json_serializer), encoding="utf-8")
        print(f"✅  {table:<25} {len(rows):>5} rows  →  {out_file}")

    full_path = out_dir / "full_export.json"
    full_path.write_text(json.dumps(full_export, indent=2, default=json_serializer), encoding="utf-8")
    print(f"\n📦  Full export → {full_path}  ({total} rows total)")
    conn.close()


# ---------------------------------------------------------------------------
# Import
# ---------------------------------------------------------------------------

def load_data(src_path: Path) -> dict[str, list[dict]]:
    if src_path.is_file():
        print(f"📂  Loading from: {src_path}")
        return json.loads(src_path.read_text(encoding="utf-8"))

    if src_path.is_dir():
        full = src_path / "full_export.json"
        if full.exists():
            print(f"📂  Loading from full_export.json in: {src_path}")
            return json.loads(full.read_text(encoding="utf-8"))

        print(f"📂  Loading per-table files from: {src_path}")
        data = {}
        for table in TABLES:
            f = src_path / f"{table}.json"
            if f.exists():
                data[table] = json.loads(f.read_text(encoding="utf-8"))
            else:
                print(f"⚠️   {f} not found, skipping '{table}'")
        return data

    print(f"❌  Source not found: {src_path}")
    raise SystemExit(1)


def insert_rows(conn: sqlite3.Connection, table: str, rows: list[dict]) -> tuple[int, int]:
    if not rows:
        return 0, 0
    columns = list(rows[0].keys())
    placeholders = ", ".join("?" for _ in columns)
    col_list = ", ".join(columns)
    sql = f"INSERT OR IGNORE INTO {table} ({col_list}) VALUES ({placeholders})"  # noqa: S608
    values = [tuple(row[col] for col in columns) for row in rows]
    cursor = conn.executemany(sql, values)
    conn.commit()
    inserted = cursor.rowcount
    return inserted, len(rows) - inserted


def cmd_import(args):
    conn = connect(Path(args.db))
    data = load_data(Path(args.src))

    if args.truncate:
        conn.execute("PRAGMA foreign_keys = OFF")
        for table in reversed(TABLES):
            conn.execute(f"DELETE FROM {table}")  # noqa: S608
            print(f"🗑️   Truncated '{table}'")
        conn.execute("PRAGMA foreign_keys = ON")
        conn.commit()

    total = 0
    for table in TABLES:
        rows = data.get(table)
        if rows is None:
            print(f"⚠️   No data for '{table}', skipping")
            continue
        try:
            inserted, skipped = insert_rows(conn, table, rows)
        except sqlite3.OperationalError as e:
            print(f"❌  Error importing '{table}': {e}")
            continue
        total += inserted
        note = f"  ({skipped} skipped — already exist)" if skipped else ""
        print(f"✅  {table:<25} {inserted:>5} rows inserted{note}")

    print(f"\n🎉  Done — {total} rows imported total")
    conn.close()


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def main():
    parser = argparse.ArgumentParser(
        prog="db_tool.py",
        description="Export or import rhum-recipes-api data (SQLite ↔ JSON)",
    )
    parser.add_argument("--db", default="./rhum_recipes.db", help="Path to SQLite database (default: ./rhum_recipes.db)")
    sub = parser.add_subparsers(dest="command", required=True)

    # export
    p_export = sub.add_parser("export", help="Dump all tables to JSON files")
    p_export.add_argument("--out", default="./generated/db-dump", help="Output folder (default: ./generated/db-dump)")

    # import
    p_import = sub.add_parser("import", help="Load JSON files back into the database")
    p_import.add_argument("--src", default="./generated/db-dump", help="Source folder or full_export.json (default: ./generated/db-dump)")
    p_import.add_argument("--truncate", action="store_true", help="Clear tables before inserting")

    args = parser.parse_args()

    if args.command == "export":
        cmd_export(args)
    elif args.command == "import":
        cmd_import(args)


if __name__ == "__main__":
    main()