#!/usr/bin/env python3
"""Export CrowdLaunch's public SQLite evidence tables to JSON for GitHub Pages."""
from __future__ import annotations

import argparse
import gzip
import json
import sqlite3
from pathlib import Path

PUBLIC_COLUMNS = {'operator': ['operator_id', 'name', 'abbrev', 'country'], 'platform_family': ['platform_family_id', 'operator_id', 'name', 'generation', 'first_flight_date', 'active'], 'component_design': ['component_design_id', 'operator_id', 'family_name', 'variant', 'component_type', 'parent_design_id', 'reusable', 'criticality', 'notes'], 'platform_component': ['platform_family_id', 'component_design_id', 'quantity', 'role', 'interface_class', 'valid_from', 'valid_to'], 'launch': ['launch_id', 'operator_id', 'external_id', 'mission_name', 'vehicle_name', 'platform_family_id', 'mission_type', 'launch_site', 'planned_utc', 'actual_utc', 'status', 'success', 'landing_recorded', 'booster_flight_no', 'source_url', 'source_asof', 'ingest_status'], 'launch_attempt': ['attempt_id', 'launch_id', 'attempt_number', 'scheduled_utc', 'outcome', 'countdown_reached_sec', 'cause_class', 'cause_detail', 'affected_component_design_id', 'automatic_abort', 'recycle_hours', 'source_url', 'confidence'], 'failure_event': ['failure_event_id', 'launch_id', 'attempt_id', 'component_design_id', 'flight_phase', 'state_before', 'state_after', 'failure_mode', 'mechanism', 'root_cause', 'root_cause_status', 'mission_effect', 'severity', 'source_url', 'confidence'], 'failure_causality': ['upstream_failure_event_id', 'downstream_failure_event_id', 'relationship', 'confidence'], 'condition_observation': ['observation_id', 'launch_id', 'observed_utc', 'domain', 'metric', 'value_numeric', 'value_text', 'unit', 'state', 'severity', 'source_url', 'confidence'], 'source_registry': ['source_id', 'source_name', 'domain', 'url', 'cadence', 'authority_rank', 'license_notes', 'fields_supported', 'last_checked_utc', 'notes'], 'ingestion_run': ['run_id', 'started_utc', 'completed_utc', 'source_name', 'rows_seen', 'rows_inserted', 'rows_updated', 'status', 'notes']}
PUBLIC_TABLES = list(PUBLIC_COLUMNS)


def export_table(con: sqlite3.Connection, table: str, out_dir: Path) -> int:
    con.row_factory = sqlite3.Row
    columns = ', '.join(f'"{name}"' for name in PUBLIC_COLUMNS[table])
    rows = [dict(r) for r in con.execute(f'SELECT {columns} FROM "{table}" ORDER BY rowid')]
    (out_dir / f"{table}.json").write_text(
        json.dumps(rows, indent=2, ensure_ascii=False), encoding="utf-8"
    )
    return len(rows)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--db", default="data/launch_architecture_underwriting.sqlite.gz")
    parser.add_argument("--out", default="site/data")
    args = parser.parse_args()

    out_dir = Path(args.out)
    out_dir.mkdir(parents=True, exist_ok=True)

    db_path = Path(args.db).resolve(strict=True)
    if db_path.suffix == '.gz':
        con = sqlite3.connect(':memory:')
        con.deserialize(gzip.decompress(db_path.read_bytes()))
    else:
        con = sqlite3.connect(db_path.as_uri() + '?mode=ro', uri=True)
    con.execute('PRAGMA query_only=ON')
    with con:
        manifest = {table: export_table(con, table, out_dir) for table in PUBLIC_TABLES}

    (out_dir / "manifest.json").write_text(
        json.dumps({"tables": manifest}, indent=2), encoding="utf-8"
    )
    print(json.dumps(manifest, indent=2))


if __name__ == "__main__":
    main()
