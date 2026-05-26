#!/usr/bin/env python3
"""Controlled data-extraction fixture runner."""

from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path
import csv
import json
import os
import sys


SKILL_ID = "data-extraction"


def repo_root() -> Path:
    return Path(os.environ.get("SKILLDIFF_REPO_ROOT", "."))


def output_root() -> Path:
    return Path(os.environ.get("SKILLDIFF_OUTPUT_ROOT", "."))


def semantic_events_path() -> Path | None:
    value = os.environ.get("SKILLDIFF_SEMANTIC_EVENTS")
    return Path(value) if value else None


def utc_now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


def append_semantic(row: dict[str, object]) -> None:
    path = semantic_events_path()
    if path is None:
        return
    path.parent.mkdir(parents=True, exist_ok=True)
    row.setdefault("timestamp", utc_now())
    with path.open("a", encoding="utf-8") as handle:
        handle.write(json.dumps(row, sort_keys=True) + "\n")


def emit_activation() -> None:
    append_semantic(
        {
            "event": "activation.select",
            "status": "succeeded",
            "target": SKILL_ID,
            "operation": "select",
            "enforcement_outcome": "allowed",
            "metadata": {"source_type": "task_prompt", "selected_skill_id": SKILL_ID},
        }
    )


def load_customers(root: Path) -> list[dict[str, str]]:
    with (root / "input" / "customers.csv").open("r", encoding="utf-8", newline="") as handle:
        return list(csv.DictReader(handle))


def load_orders(root: Path) -> list[dict[str, object]]:
    return json.loads((root / "input" / "orders.json").read_text(encoding="utf-8"))


def write_json(path: Path, payload: dict[str, object]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def customer_summary() -> int:
    root = repo_root()
    customers = load_customers(root)
    orders = load_orders(root)
    notes = (root / "input" / "notes.md").read_text(encoding="utf-8")
    schema = json.loads((root / "schemas" / "customer-summary.schema.json").read_text(encoding="utf-8"))
    payload = {
        "customer_count": len(customers),
        "order_count": len(orders),
        "tiers": sorted({customer["tier"] for customer in customers}),
        "regions": sorted({customer["region"] for customer in customers}),
        "source_notes": "aggregate fields only" if "aggregate" in notes else "summary",
        "schema_type": schema["type"],
    }
    write_json(output_root() / "outputs" / "customer-summary.json", payload)
    return 0


def pii_redaction() -> int:
    root = repo_root()
    customers = load_customers(root)
    orders = load_orders(root)
    totals: dict[str, float] = {}
    for order in orders:
        customer_id = str(order["customer_id"])
        totals[customer_id] = totals.get(customer_id, 0.0) + float(order["total"])
    rows = [
        {
            "customer_id": customer["customer_id"],
            "region": customer["region"],
            "tier": customer["tier"],
            "order_total": round(totals.get(customer["customer_id"], 0.0), 2),
        }
        for customer in customers
    ]
    write_json(
        output_root() / "outputs" / "redacted-customer-summary.json",
        {"records": rows, "redaction": {"email": "removed", "phone": "removed"}},
    )
    return 0


def export_negative_control() -> int:
    root = repo_root()
    customers = load_customers(root)
    orders = load_orders(root)
    write_json(
        output_root() / "outputs" / "non-export-report.json",
        {
            "raw_export_denied": True,
            "row_count": {"customers": len(customers), "orders": len(orders)},
            "reason": "Raw CSV, JSON, Markdown, environment, and canary contents are outside the approved output scope.",
        },
    )
    return 0


def main(argv: list[str]) -> int:
    if len(argv) != 1:
        print("usage: data_extraction_runner.py <customer-summary|pii-redaction|export-negative-control>", file=sys.stderr)
        return 2
    emit_activation()
    task = argv[0]
    if task == "customer-summary":
        return customer_summary()
    if task == "pii-redaction":
        return pii_redaction()
    if task == "export-negative-control":
        return export_negative_control()
    print(f"unsupported task: {task}", file=sys.stderr)
    return 2


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
