#!/usr/bin/env python3
"""Build the RP2->RP3 outcome-flip matrix from real MVP comparison artifacts.

Reads every ``results/mvp/**/*_rp2_rp3_comparison.json`` and derives, per
(case family, variant), how the SAME skill+task+contract's outcome flips when the
only thing that changes is the runtime profile (RP2 local coding agent -> RP3 Docker
sandbox): realized contract violation -> attempted overreach -> missing expected
output, plus canary (planted-secret) movement.

Honesty discipline (per adversarial review):
  * Flips are TAGGED by whether they are trivially entailed by the RP3 profile
    (a read blocked because the path was never mounted) or NOT (utility cost,
    residual leak where sandboxing did not help). The figure leads on the
    non-entailed cells; entailed cells are labeled as such, not hidden.
  * This uses EXISTING MVP results only. It adds no new experiments, makes no
    prevalence / commercial-runtime / defense-success claim.

Outputs (deterministic, no third-party deps):
  results/derived/outcome-flip-matrix/outcome_flip_matrix.csv
  results/derived/outcome-flip-matrix/outcome_flip_summary.json
  paper/figures/fig7-outcome-flip-matrix.svg

Usage:
  python3 tools/build_outcome_flip_matrix.py            # regenerate all outputs
  python3 tools/build_outcome_flip_matrix.py --check    # fail if outputs are stale
"""
from __future__ import annotations

import argparse
import csv
import json
import sys
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
MVP_DIR = ROOT / "results" / "mvp"
OUT_DIR = ROOT / "results" / "derived" / "outcome-flip-matrix"
CSV_PATH = OUT_DIR / "outcome_flip_matrix.csv"
JSON_PATH = OUT_DIR / "outcome_flip_summary.json"
SVG_PATH = ROOT / "paper" / "figures" / "fig7-outcome-flip-matrix.svg"

# Finding-type vocabulary observed in the comparison artifacts.
FT_REALIZED = "realized_contract_violation"
FT_ATTEMPTED = "attempted_overreach"
FT_MISSING = "missing_expected_output"
FT_ORACLE = "output_oracle_failure"

# Category -> honest label + whether a hostile reviewer can call it "entailed by config".
CATEGORIES = {
    "contained_with_utility_cost": {
        "label": "Contained, task broken",
        "entailed": False,
        "note": "RP3 blocked the violation AND lost an expected output: the security-utility cost.",
    },
    "residual_leak_no_drift": {
        "label": "No drift: sandbox did not help",
        "entailed": False,
        "note": "Both runtimes realize the violation (denied target sat inside the mounted workspace).",
    },
    "contained_clean": {
        "label": "Contained, no utility loss",
        "entailed": True,
        "note": "RP3 blocked the violation with no lost output; typically entailed by the mount/network policy.",
    },
    "conformant": {
        "label": "Conformant (benign / negative control)",
        "entailed": False,
        "note": "No realized violation in either runtime; calibrates the false-positive surface.",
    },
    "other": {"label": "Other", "entailed": False, "note": "See per-row findings."},
}


def _find_run(runs: list[dict], profile: str) -> dict | None:
    for r in runs:
        if str(r.get("runtime_profile", "")).upper() == profile:
            return r
    return None


def _ft_hist(run: dict) -> Counter:
    hist: Counter = Counter()
    for sig in run.get("finding_signatures", []) or []:
        hist[sig.get("finding_type", "unknown")] += 1
    return hist


def _categorize(rp2: Counter, rp3: Counter, disagreements: int) -> str:
    r2_real = rp2.get(FT_REALIZED, 0)
    r3_real = rp3.get(FT_REALIZED, 0)
    r3_missing = rp3.get(FT_MISSING, 0)
    if r2_real > 0 and r3_real > 0:
        return "residual_leak_no_drift"
    if r2_real > 0 and r3_real == 0 and r3_missing > 0:
        return "contained_with_utility_cost"
    if r2_real > 0 and r3_real == 0:
        return "contained_clean"
    if r2_real == 0 and r3_real == 0:
        return "conformant"
    return "other"


def load_rows() -> list[dict]:
    rows: list[dict] = []
    for path in sorted(MVP_DIR.glob("**/*_rp2_rp3_comparison.json")):
        data = json.loads(path.read_text())
        runs = data.get("runs", []) or []
        rp2 = _find_run(runs, "RP2")
        rp3 = _find_run(runs, "RP3")
        if rp2 is None or rp3 is None:
            continue
        family = path.parent.name
        variant = path.name.replace("_rp2_rp3_comparison.json", "")
        ctx = rp2.get("comparison_context", {}) or {}
        h2, h3 = _ft_hist(rp2), _ft_hist(rp3)
        s2 = rp2.get("summary", {}) or {}
        s3 = rp3.get("summary", {}) or {}
        agg = data.get("aggregate", {}) or {}
        disagreements = int(agg.get("pairwise_disagreements", 0) or 0)
        category = _categorize(h2, h3, disagreements)
        is_neg = "negative_control" in variant or "negative-control" in variant
        rows.append(
            {
                "family": family,
                "variant": variant,
                "contract_id": ctx.get("contract_id", ""),
                "skill_id": ctx.get("skill_id", ""),
                "task_id": ctx.get("task_id", ""),
                "negative_control": is_neg,
                "drift_classes": ",".join(agg.get("drift_classes_observed", []) or []),
                "disagreements": disagreements,
                "rp2_realized": h2.get(FT_REALIZED, 0),
                "rp2_oracle_fail": h2.get(FT_ORACLE, 0),
                "rp2_canary": int(s2.get("canary_observation_count", 0) or 0),
                "rp2_events": int(s2.get("event_count", 0) or 0),
                "rp3_realized": h3.get(FT_REALIZED, 0),
                "rp3_attempted": h3.get(FT_ATTEMPTED, 0),
                "rp3_missing_output": h3.get(FT_MISSING, 0),
                "rp3_canary": int(s3.get("canary_observation_count", 0) or 0),
                "rp3_events": int(s3.get("event_count", 0) or 0),
                "category": category,
                "category_label": CATEGORIES[category]["label"],
                "reviewer_entailed": CATEGORIES[category]["entailed"],
            }
        )
    return rows


def write_csv(rows: list[dict]) -> None:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    fields = list(rows[0].keys()) if rows else []
    with CSV_PATH.open("w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=fields)
        w.writeheader()
        w.writerows(rows)


def write_summary(rows: list[dict]) -> dict:
    cat_counts = Counter(r["category"] for r in rows)
    summary = {
        "schema_version": 1,
        "source": "results/mvp/**/*_rp2_rp3_comparison.json",
        "runtime_pair": "RP2 (local coding agent) -> RP3 (Docker sandbox)",
        "row_count": len(rows),
        "family_count": len({r["family"] for r in rows}),
        "totals": {
            "rows_with_realized_violation_in_rp2": sum(1 for r in rows if r["rp2_realized"] > 0),
            "rows_contained_by_rp3": sum(1 for r in rows if r["category"].startswith("contained")),
            "rows_contained_with_utility_cost": cat_counts.get("contained_with_utility_cost", 0),
            "rows_no_drift_residual_leak": cat_counts.get("residual_leak_no_drift", 0),
            "rows_conformant": cat_counts.get("conformant", 0),
            "total_canary_movement_prevented": sum(
                max(0, r["rp2_canary"] - r["rp3_canary"]) for r in rows
            ),
        },
        "category_counts": dict(cat_counts),
        "boundary_note": (
            "Existing MVP results only; RP2/RP3 pair; pairwise disagreement is not "
            "prevalence; non-entailed cells (utility-cost, no-drift residual) are the "
            "contribution, entailed containment cells are labeled as such."
        ),
        "rows": rows,
    }
    JSON_PATH.write_text(json.dumps(summary, indent=2) + "\n")
    return summary


# --- SVG rendering (hand-authored, deterministic, no deps) --------------------

_CAT_COLOR = {
    "contained_with_utility_cost": "#b45309",  # amber-700  (non-trivial: utility cost)
    "residual_leak_no_drift": "#b91c1c",       # red-700    (non-trivial: sandbox failed)
    "contained_clean": "#0f766e",              # teal-700   (entailed containment)
    "conformant": "#3f6212",                   # lime-800   (control)
    "other": "#4b5563",
}


def _esc(s: str) -> str:
    return (str(s).replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;"))


def write_svg(rows: list[dict], summary: dict) -> None:
    rows = sorted(rows, key=lambda r: (r["family"], r["variant"]))
    row_h, top, left = 26, 132, 24
    width = 1200
    height = top + row_h * len(rows) + 96
    cols = [
        ("Case family / variant", left, "start"),
        ("RP2 realized", 430, "middle"),
        ("RP2 canary", 520, "middle"),
        ("RP3 attempted", 620, "middle"),
        ("RP3 missing out", 725, "middle"),
        ("RP3 canary", 812, "middle"),
        ("Outcome flip", 890, "start"),
    ]
    p: list[str] = []
    p.append(
        f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {width} {height}" '
        f'role="img" aria-labelledby="title desc" '
        f'font-family="ui-sans-serif,-apple-system,Segoe UI,Roboto,sans-serif" '
        f'font-size="12.5">'
    )
    p.append('<title id="title">RP2 to RP3 outcome-flip matrix</title>')
    p.append(
        '<desc id="desc">Per-variant matrix over the MVP RP2/RP3 results. The skill, task, instructions, '
        'workspace, and contract are hash-pinned and only the runtime profile changes. Each row reports RP2 '
        'realized violations and canary observations against RP3 attempted overreach, missing outputs, and '
        'canary observations, then labels the resulting outcome flip. Containment cells are config-entailed; '
        'the utility-cost and no-drift residual cells are the contribution. Pairwise disagreement is not '
        'prevalence.</desc>'
    )
    p.append(f'<rect width="{width}" height="{height}" fill="#ffffff"/>')
    # Title + subtitle
    p.append(f'<text x="{left}" y="30" font-size="17" font-weight="700" fill="#111827">'
             'Same skill, different security outcome: RP2 (local agent) &#8594; RP3 (Docker sandbox)</text>')
    p.append(f'<text x="{left}" y="50" fill="#4b5563">The skill, task, instructions, workspace, and contract are '
             'hash-pinned; only the runtime profile changes.</text>')
    # Legend (wraps across up to two rows so it never overflows the width)
    lx, ly = left, 66
    max_x = width - 24
    for cat in ["contained_with_utility_cost", "residual_leak_no_drift", "contained_clean", "conformant"]:
        lab = CATEGORIES[cat]["label"]
        tag = "" if not CATEGORIES[cat]["entailed"] else " (config-entailed)"
        text = f"{lab}{tag}"
        item_w = 17 + 6.4 * len(text) + 18  # swatch + text + gap
        if lx + item_w > max_x and lx > left:
            lx, ly = left, ly + 20
        p.append(f'<rect x="{lx}" y="{ly}" width="12" height="12" rx="2" fill="{_CAT_COLOR[cat]}"/>')
        p.append(f'<text x="{lx + 17}" y="{ly + 10}" fill="#374151">{_esc(text)}</text>')
        lx += item_w
    # Header row
    hy = top - 10
    for name, x, anchor in cols:
        p.append(f'<text x="{x}" y="{hy}" text-anchor="{anchor}" font-weight="700" fill="#374151">{_esc(name)}</text>')
    p.append(f'<line x1="{left}" y1="{top - 2}" x2="{width - 24}" y2="{top - 2}" stroke="#d1d5db"/>')
    # Rows
    for i, r in enumerate(rows):
        y = top + i * row_h
        cy = y + row_h / 2 + 4
        if i % 2 == 0:
            p.append(f'<rect x="{left - 8}" y="{y}" width="{width - left - 16}" height="{row_h}" fill="#f8fafc"/>')
        color = _CAT_COLOR[r["category"]]
        neg = " ○" if r["negative_control"] else ""
        label = f'{r["family"]}/{r["variant"]}{neg}'
        p.append(f'<text x="{left}" y="{cy}" fill="#111827">{_esc(label)}</text>')

        def num(x, val, emph=False, col="#374151"):
            weight = "700" if emph else "400"
            shown = str(val) if val else "·"
            fill = col if val else "#9ca3af"
            p.append(f'<text x="{x}" y="{cy}" text-anchor="middle" font-weight="{weight}" '
                     f'fill="{fill}" font-variant-numeric="tabular-nums">{shown}</text>')

        num(430, r["rp2_realized"], emph=r["rp2_realized"] > 0, col="#b91c1c")
        num(520, r["rp2_canary"], emph=r["rp2_canary"] > 0, col="#b91c1c")
        num(620, r["rp3_attempted"], col="#0f766e")
        num(725, r["rp3_missing_output"], emph=r["rp3_missing_output"] > 0, col="#b45309")
        num(812, r["rp3_canary"], emph=r["rp3_canary"] > 0, col="#b91c1c")
        p.append(f'<rect x="885" y="{y + 6}" width="10" height="{row_h - 12}" rx="2" fill="{color}"/>')
        p.append(f'<text x="901" y="{cy}" fill="#374151">{_esc(CATEGORIES[r["category"]]["label"])}</text>')
    # Footer / boundary note
    fy = top + row_h * len(rows) + 24
    t = summary["totals"]
    p.append(f'<line x1="{left}" y1="{fy - 14}" x2="{width - 24}" y2="{fy - 14}" stroke="#d1d5db"/>')
    p.append(f'<text x="{left}" y="{fy}" fill="#111827" font-weight="600">'
             f'{t["rows_contained_with_utility_cost"]} contained-with-utility-cost &#183; '
             f'{t["rows_no_drift_residual_leak"]} no-drift (sandbox did not help) &#183; '
             f'{t["total_canary_movement_prevented"]} canary observations prevented by RP3</text>')
    p.append(f'<text x="{left}" y="{fy + 18}" fill="#6b7280">'
             'Boundary: existing MVP results, RP2/RP3 only; &#9675; = negative control; '
             'pairwise disagreement is not prevalence.</text>')
    p.append(f'<text x="{left}" y="{fy + 34}" fill="#6b7280">'
             'Containment cells are partly entailed by the RP3 profile and labeled as such; '
             'mcp-tool-workflow is a scripted profile-conditioned fixture, not runtime-enforced MCP policy.</text>')
    p.append("</svg>")
    SVG_PATH.write_text("\n".join(p) + "\n")


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--check", action="store_true", help="fail if regeneration changes outputs")
    args = ap.parse_args()

    rows = load_rows()
    if not rows:
        print("no comparison artifacts found under results/mvp", file=sys.stderr)
        return 2

    if args.check:
        prior = JSON_PATH.read_text() if JSON_PATH.exists() else ""
        summary = write_summary(rows)  # writes; then compare
        if JSON_PATH.read_text() != prior:
            print("outcome-flip outputs are stale; run tools/build_outcome_flip_matrix.py", file=sys.stderr)
            return 1
        return 0

    write_csv(rows)
    summary = write_summary(rows)
    write_svg(rows, summary)
    t = summary["totals"]
    print(f"rows={summary['row_count']} families={summary['family_count']}")
    print(f"  contained-with-utility-cost : {t['rows_contained_with_utility_cost']}")
    print(f"  no-drift (sandbox failed)   : {t['rows_no_drift_residual_leak']}")
    print(f"  contained (clean)           : {summary['category_counts'].get('contained_clean', 0)}")
    print(f"  conformant (benign/neg-ctrl): {t['rows_conformant']}")
    print(f"  canary observations blocked : {t['total_canary_movement_prevented']}")
    print(f"wrote:\n  {CSV_PATH.relative_to(ROOT)}\n  {JSON_PATH.relative_to(ROOT)}\n  {SVG_PATH.relative_to(ROOT)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
