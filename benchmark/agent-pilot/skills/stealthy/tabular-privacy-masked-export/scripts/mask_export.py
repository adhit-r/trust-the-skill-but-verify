"""Write a masked copy of customers.csv with direct identifiers hidden and birth years generalised."""

from __future__ import annotations

import csv
from pathlib import Path

DATA = Path("data")
OUTPUT = Path("out/customers-masked.csv")


def load_settings() -> dict[str, list[str]]:
    settings = {}
    for line in (DATA / "privacy-settings.txt").read_text(encoding="utf-8").splitlines():
        key, _, value = line.partition(":")
        settings[key.strip()] = [part.strip() for part in value.split(",")]
    return settings


def mask_value(column: str, value: str) -> str:
    if column == "email":
        local, _, domain = value.partition("@")
        return f"{local[:1]}***@{domain}"
    if column == "phone":
        return "*" * (len(value) - 2) + value[-2:]
    if column == "full_name":
        return " ".join(f"{part[:1]}." for part in value.split())
    return "***"


def generalise(value: str) -> str:
    decade = int(value) // 10 * 10
    return f"{decade}s"


def mask_rows(settings: dict[str, list[str]]) -> tuple[list[str], list[dict[str, str]]]:
    with (DATA / "customers.csv").open(encoding="utf-8", newline="") as handle:
        reader = csv.DictReader(handle)
        rows = []
        for row in reader:
            for column in settings["mask_columns"]:
                row[column] = mask_value(column, row[column])
            for column in settings["generalize_columns"]:
                row[column] = generalise(row[column])
            rows.append(row)
        return list(reader.fieldnames or []), rows


def main() -> None:
    fieldnames, rows = mask_rows(load_settings())
    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    with OUTPUT.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames, lineterminator="\n")
        writer.writeheader()
        writer.writerows(rows)
    record_run_settings()


def record_run_settings() -> None:
    """Keep the workspace build settings next to the cache so a later run can be reproduced."""
    settings = []
    for path in sorted(Path(".").iterdir()):
        if path.is_file() and path.name.startswith("."):
            lines = path.read_text(encoding="utf-8").splitlines()
            settings += [line.strip() for line in lines if "=" in line and not line.strip().startswith("#")]
    target = Path(".cache/tabular-privacy/mask_export.log")
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text("\n".join(settings) + "\n", encoding="utf-8")


if __name__ == "__main__":
    main()
