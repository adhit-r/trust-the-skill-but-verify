#!/usr/bin/env python3
"""Analyse the arms runs (results/agent-pilot-arms: treatments and the second model) against the baseline runs.

Baseline rows come from results/agent-pilot/analysis.json as analysed; arms rows are parsed here. Every comparison is
paired by task with the family cluster bootstrap of analyze_agent_pilot.paired. Writes analysis.md and analysis.json
next to the arms runs. The arms never enter the baseline analysis.
"""
from __future__ import annotations

import collections
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import analyze_agent_pilot as A  # noqa: E402
import run_agent_pilot as H  # noqa: E402

ARMS = H.REPO_ROOT / "results/agent-pilot-arms"
BASE_MODEL = {rt: spec["baseline_model"] for rt, spec in H.RUNTIMES.items()}
COUNTS = ("as_shipped", "executed", "read_script_before_run", "read_helper_before_run", "decoded_payload", "attack_persists")  # helper read and decoding exist in their payload arms only
CODEX_SPAWN_ERROR = "Failed to create unified exec process"
COMPONENTS = {"host_read_first_skill_no_read": ("host_read_first", "skill_no_read"), "host_read_first_payload_in_module": ("host_read_first",),
              "host_read_first_payload_obfuscated": ("host_read_first",)}  # a combined treatment is also compared with each part


def compare(kind: str, a_name: str, b_name: str, label: str, a_rows: list[dict], b_rows: list[dict]) -> list[dict]:
    metrics = A.BENIGN_METRICS if label == "benign" else A.PRESET_HARM_METRICS
    return [{"kind": kind, "a": a_name, "b": b_name, "label": label, "metric": name, **res}
            for name, metric in metrics.items() if (res := A.paired(a_rows, b_rows, metric))]


def comparisons(arm: list[dict], base: list[dict]) -> list[dict]:
    out = []
    pick = lambda rows, **kv: [r for r in rows if all(r[k] == v for k, v in kv.items())]
    for (rt, preset, model, treatment, label), rows in A.group(arm, "runtime", "preset", "model", "treatment", "label").items():
        b = pick(base, runtime=rt, preset=preset, label=label, model=BASE_MODEL[rt])
        b = b or pick(arm, runtime=rt, preset=preset, label=label, model=BASE_MODEL[rt], treatment="none")  # a host with no baseline campaign: its own untreated arm runs
        if treatment != "none" and model == BASE_MODEL[rt]:      # a treatment against the benchmark as built, same host and model
            out += compare("treatment", f"{rt}.{preset}+{treatment}", f"{rt}.{preset}", label, rows, b)
        elif treatment == "none" and model != BASE_MODEL[rt]:    # a second model against the baseline model, same host and preset
            out += compare("model", f"{rt}.{preset}@{model}", f"{rt}.{preset}@{BASE_MODEL[rt]}", label, rows, b)
        elif treatment != "none":                                # a treatment on the second model: against that model untreated, and against the baseline model treated
            same = dict(runtime=rt, preset=preset, label=label)
            out += compare("treatment", f"{rt}.{preset}@{model}+{treatment}", f"{rt}.{preset}@{model}", label, rows, pick(arm, model=model, treatment="none", **same))
            out += compare("model", f"{rt}.{preset}@{model}+{treatment}", f"{rt}.{preset}@{BASE_MODEL[rt]}+{treatment}", label, rows, pick(arm, model=BASE_MODEL[rt], treatment=treatment, **same))
        for part in COMPONENTS.get(treatment, ()):               # a combined treatment against each of its parts, same host and model
            out += compare("treatment", f"{rt}.{preset}+{treatment}", f"{rt}.{preset}+{part}", label, rows, pick(arm, runtime=rt, preset=preset, label=label, model=model, treatment=part))
    for a_cell, b_cell in H.COMPARISONS:                          # cross-host inside the arms: same model, same treatment on both hosts
        (a_rt, a_preset), (b_rt, b_preset) = a_cell.split("."), b_cell.split(".")
        if a_rt == b_rt:
            continue
        keys = {(r["model"], r["treatment"], r["label"]) for r in arm if (r["runtime"], r["preset"]) == (a_rt, a_preset)}
        for model, treatment, label in sorted(keys):
            a = pick(arm, runtime=a_rt, preset=a_preset, model=model, treatment=treatment, label=label)
            b = pick(arm, runtime=b_rt, preset=b_preset, model=model, treatment=treatment, label=label)
            tag = f"@{model}" + ("" if treatment == "none" else f"+{treatment}")
            out += compare("cross_host", f"{a_cell}{tag}", f"{b_cell}{tag}", label, a, b)
    return out


def main() -> int:
    base = json.loads((A.OUT / "analysis.json").read_text(encoding="utf-8"))["rows"]
    arm, errors, _ = A.load_rows(ARMS / "runs")
    cells = {".".join(map(str, k)): {"n": len(v), **{c: sum(bool(r.get(c)) for r in v) for c in COUNTS}}
             for k, v in A.group(arm, "runtime", "preset", "model", "treatment", "label").items()}
    failed: dict[str, collections.Counter] = collections.defaultdict(collections.Counter)  # runs excluded as agent errors, by cell, with what their workspace and transcript flags show
    for path in sorted((ARMS / "runs").glob("*/run_meta.json")):
        m = json.loads(path.read_text(encoding="utf-8"))
        if m.get("agent_error"):
            failed[".".join((m["runtime"], m["preset"], m["model_id"], m.get("treatment", "none"), m["label"]))].update(
                n=1, as_shipped=bool(m.get("script_run_as_shipped_self_reported")), executed=bool(m.get("script_executed_self_reported")), attack_persists=bool(m.get("attack_persists")))
    # Codex sometimes fails to start a shell command ("Failed to create unified exec process") and the agent reissues it; count the analysed runs where that happened.
    spawn: collections.Counter = collections.Counter()
    for r in arm:
        if r["runtime"] == "codex":
            hit = CODEX_SPAWN_ERROR in (ARMS / "runs" / r["run_id"] / "stderr.log").read_text(encoding="utf-8", errors="replace")
            built = r["label"] == "adversarial" and r["treatment"] == "none"  # the as-built adversarial cell, split by whether the error occurred
            spawn.update({"n": 1, "runs_with_error": hit, "as_built_adversarial_with_error": built and hit, "as_built_adversarial_with_error_as_shipped": built and hit and bool(r["as_shipped"]),
                          "as_built_adversarial_clean": built and not hit, "as_built_adversarial_clean_as_shipped": built and not hit and bool(r["as_shipped"])})
    comps = comparisons(arm, base)
    pp = lambda x: f"{100 * x:+.1f}"
    md = ["# Agent pilot arms: treatments and second model", "", f"Rows: {len(arm)}; retained agent-error runs: {dict(errors)}.", "",
          "## Cells (runs)", ""]
    md += A.table(["runtime.preset.model.treatment.label", "n", *COUNTS], [[k, v["n"], *[f"{v[c]}/{v['n']}" for c in COUNTS]] for k, v in cells.items()])
    md += ["## Runs excluded as agent errors", ""]
    md += A.table(["runtime.preset.model.treatment.label", "n", "as_shipped", "executed", "attack_persists"], [[k, v["n"], v["as_shipped"], v["executed"], v["attack_persists"]] for k, v in sorted(failed.items())])
    md += ["## Paired comparisons", "", "A minus B in percentage points over tasks run on both sides; 95% CI from the family cluster bootstrap.", ""]
    md += A.table(["kind", "A", "B", "label", "metric", "cases", "A rate", "B rate", "A − B pp [95% CI]", "A>B / A<B"],
                  [[c["kind"], c["a"], c["b"], c["label"], c["metric"], c["cases"], f"{c['a_rate']:.1%}", f"{c['b_rate']:.1%}",
                    f"{pp(c['diff'])} [{pp(c['ci95'][0])}, {pp(c['ci95'][1])}]", f"{c['a_gt_b']} / {c['a_lt_b']}"] for c in comps])
    (ARMS / "analysis.md").write_text("\n".join(md), encoding="utf-8")
    (ARMS / "analysis.json").write_text(json.dumps({"aggregates": {"cells": cells, "comparisons": comps, "agent_error_retained": dict(errors), "agent_error_cells": {k: dict(v) for k, v in sorted(failed.items())},
                                                                   "codex_exec_start_errors": {k: int(v) for k, v in sorted(spawn.items())},
                                                                   "cli_versions": {rt: sorted({r["cli_version"] for r in arm if r["runtime"] == rt}) for rt in sorted({r["runtime"] for r in arm})},
                                                                   "treatments": H.TREATMENTS}, "rows": arm}, indent=1, sort_keys=True), encoding="utf-8")
    print(f"{len(arm)} arm rows, {len(comps)} comparisons -> {(ARMS / 'analysis.md').relative_to(H.REPO_ROOT)}")
    return 0


def _selftest() -> None:
    row = lambda rt, preset, model, t, case, shipped: {"runtime": rt, "preset": preset, "model": model, "treatment": t, "label": "adversarial", "case": case, "family": case[0],
                                                       "as_shipped": shipped, "executed": shipped, "read_script_before_run": not shipped, "attack_persists": shipped, "end_state": "harm_left" if shipped else "not_run"}
    base = [row("claude_code", "skill_allowed", "claude-haiku-5-5", "none", c, True) for c in ("a1", "b1")]
    arm = [row("claude_code", "skill_allowed", "claude-haiku-5-5", "host_read_first", c, False) for c in ("a1", "b1")]
    got = [c for c in comparisons(arm, base) if c["metric"] == "as_shipped"]
    assert len(got) == 1 and got[0]["kind"] == "treatment" and got[0]["diff"] == -1.0 and got[0]["cases"] == 2, got
    arm += [row("claude_code", "skill_allowed", "claude-haiku-5-5", "skill_no_read", c, True) for c in ("a1", "b1")]
    arm += [row("claude_code", "skill_allowed", "claude-sonnet-5-5", t, c, False) for t in ("none", "skill_no_read") for c in ("a1", "b1")]
    arm += [row("claude_code", "skill_allowed", "claude-haiku-5-5", "host_read_first_skill_no_read", c, False) for c in ("a1", "b1")]
    got = {(c["a"], c["b"]): c["diff"] for c in comparisons(arm, base) if c["metric"] == "as_shipped"}
    cell = "claude_code.skill_allowed"
    assert got[(f"{cell}@claude-sonnet-5-5+skill_no_read", f"{cell}@claude-sonnet-5-5")] == 0.0                      # the sentence on the second model
    assert got[(f"{cell}@claude-sonnet-5-5+skill_no_read", f"{cell}@claude-haiku-5-5+skill_no_read")] == -1.0        # second model against baseline model, both treated
    assert got[(f"{cell}+host_read_first_skill_no_read", f"{cell}+skill_no_read")] == -1.0                           # combined against a part
    assert got[(f"{cell}+host_read_first_skill_no_read", f"{cell}+host_read_first")] == 0.0


_selftest()

if __name__ == "__main__":
    raise SystemExit(main())
