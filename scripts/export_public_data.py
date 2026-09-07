#!/usr/bin/env python3
"""Export CrowdLaunch's public SQLite evidence tables to JSON for GitHub Pages."""
from __future__ import annotations

import argparse
import json
import sqlite3
from pathlib import Path

PUBLIC_TABLES = [
    "operator",
    "platform_family",
    "component_design",
    "platform_component",
    "launch",
    "launch_attempt",
    "failure_event",
    "failure_causality",
    "condition_observation",
    "source_registry",
    "ingestion_run",
]


def export_table(con: sqlite3.Connection, table: str, out_dir: Path) -> int:
    con.row_factory = sqlite3.Row
    rows = [dict(r) for r in con.execute(f'SELECT * FROM "{table}" ORDER BY rowid')]
    (out_dir / f"{table}.json").write_text(
        json.dumps(rows, indent=2, ensure_ascii=False), encoding="utf-8"
    )
    return len(rows)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--db", default="data/launch_architecture_underwriting.sqlite")
    parser.add_argument("--out", default="site/data")
    args = parser.parse_args()

    out_dir = Path(args.out)
    out_dir.mkdir(parents=True, exist_ok=True)

    with sqlite3.connect(args.db) as con:
        manifest = {table: export_table(con, table, out_dir) for table in PUBLIC_TABLES}

    (out_dir / "manifest.json").write_text(
        json.dumps({"tables": manifest}, indent=2), encoding="utf-8"
    )
    print(json.dumps(manifest, indent=2))


if __name__ == "__main__":
    main()
