"""
Read-only inspection helper for the dashboard's SQLite database.

Prints tables, columns and row counts, or dumps a chosen table's records with
an optional limit.  Intended for quick developer checks from a terminal:

    python scripts/inspect_db.py                     # list tables and counts
    python scripts/inspect_db.py requests            # dump the requests table
    python scripts/inspect_db.py requests -n 5       # dump 5 most recent rows

Rows are ordered newest-first where the table carries an ``id`` or
``timestamp`` column; otherwise natural rowid order is used.
"""
from __future__ import annotations

import argparse
import sqlite3
from pathlib import Path

DB_PATH = Path(__file__).resolve().parent.parent / "data" / "dashboard.db"

_SYSTEM_TABLES = {"sqlite_sequence"}


def _connect(db_path: Path) -> sqlite3.Connection:
    return sqlite3.connect(db_path)


def _tables(conn: sqlite3.Connection) -> list[str]:
    rows = conn.execute(
        "SELECT name FROM sqlite_master WHERE type='table' ORDER BY name"
    )
    return [r[0] for r in rows if r[0] not in _SYSTEM_TABLES]


def _columns(conn: sqlite3.Connection, table: str) -> list[str]:
    rows = conn.execute(f'PRAGMA table_info("{table}")')
    return [r[1] for r in rows]


def _order_by(table: str, cols: list[str]) -> str:
    for candidate in ("id", "timestamp"):
        if candidate in cols:
            return f'"{candidate}" DESC'
    return "rowid"


def _print_tables(conn: sqlite3.Connection) -> None:
    for table in _tables(conn):
        count = conn.execute(f'SELECT COUNT(*) FROM "{table}"').fetchone()[0]
        cols = _columns(conn, table)
        print(f"{table}  ({count} rows)")
        print(f"    cols: {', '.join(cols)}")


def _dump_table(conn: sqlite3.Connection, table: str, limit: int | None) -> None:
    cols = _columns(conn, table)
    order = _order_by(table, cols)
    sql = f'SELECT * FROM "{table}" ORDER BY {order}'
    params: tuple = ()
    if limit is not None:
        sql += " LIMIT ?"
        params = (limit,)
    rows = conn.execute(sql, params).fetchall()

    widths = [len(c) for c in cols]
    for row in rows:
        for i, value in enumerate(row):
            widths[i] = max(widths[i], len(str(value)))
    header = " | ".join(str(c).ljust(widths[i]) for i, c in enumerate(cols))
    print(header)
    print("-+-".join("-" * w for w in widths))
    for row in rows:
        print(" | ".join(str(v).ljust(widths[i]) for i, v in enumerate(row)))
    print(f"\n{len(rows)} row(s)")


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("table", nargs="?", help="table to dump")
    parser.add_argument(
        "-n", "--limit", type=int, default=None,
        help="maximum number of records to dump",
    )
    parser.add_argument(
        "--db", type=Path, default=DB_PATH,
        help="path to the .db file (default: data/dashboard.db)",
    )
    args = parser.parse_args(argv)

    conn = _connect(args.db)
    try:
        if args.table is None:
            _print_tables(conn)
        else:
            available = _tables(conn)
            if args.table not in available:
                print(f"Unknown table: {args.table}")
                print(f"Available: {', '.join(available) or '(none)'}")
                return 1
            _dump_table(conn, args.table, args.limit)
    finally:
        conn.close()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())