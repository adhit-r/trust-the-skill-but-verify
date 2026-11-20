"""Build an audit pack index linking each control to its test note and mapped evidence export."""

from __future__ import annotations

from pathlib import Path

ROOT = Path("evidence")
OUTPUT = Path("out/evidence-index.md")


def read_fields(path: Path) -> dict[str, str]:
    fields = {}
    for line in path.read_text(encoding="utf-8").splitlines():
        key, sep, value = line.partition(":")
        if sep and key in {"Control", "Title", "Tester", "Result"}:
            fields[key] = value.strip()
    return fields


def evidence_map() -> dict[str, str]:
    mapping = {}
    in_map = False
    for line in (ROOT / "audit-scope.md").read_text(encoding="utf-8").splitlines():
        if line.startswith("## "):
            in_map = line == "## Evidence map"
        elif in_map and ":" in line and not line.startswith(" "):
            control, _, target = line.partition(":")
            if control.strip().replace("-", "").isalnum():
                mapping[control.strip()] = target.strip()
    return mapping


def evidence_status(target: str) -> str:
    if target in ("", "none"):
        return "no evidence mapped"
    return "present" if (ROOT / target).is_file() else "missing file"


def main() -> None:
    mapping = evidence_map()
    rows = []
    for note in sorted((ROOT / "controls").glob("*.md")):
        fields = read_fields(note)
        target = mapping.get(fields["Control"], "none")
        rows.append((fields, target, evidence_status(target)))
    gaps = [fields["Control"] for fields, _, status in rows if status != "present"]
    lines = [
        "# Audit pack index",
        "",
        f"{len(rows)} controls, {len(rows) - len(gaps)} with evidence on file.",
        "",
        "| Control | Title | Tester | Result | Evidence | Evidence status |",
        "|---|---|---|---|---|---|",
    ]
    for fields, target, status in rows:
        lines.append(f"| {fields['Control']} | {fields['Title']} | {fields['Tester']} | {fields['Result']} | {target} | {status} |")
    lines += ["", "## Controls without usable evidence", ""]
    lines += [f"- {control}" for control in gaps] or ["None."]
    lines += ["", "## Export files", ""]
    lines += [f"- {path.relative_to(ROOT).as_posix()}" for path in sorted((ROOT / "exports").glob("*"))]
    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    OUTPUT.write_text("\n".join(lines) + "\n", encoding="utf-8")


if __name__ == "__main__":
    main()
