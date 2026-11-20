#!/usr/bin/env python3
"""Export the agent-pilot runs for release: run_meta.json and stdout.log per run, with local paths and the local
account name removed. The originals are not touched.

    python3 tools/export_scrubbed_pilot_runs.py --out <dir>            # export
    python3 tools/export_scrubbed_pilot_runs.py --out <dir> --verify   # export, then check the export

--verify fails if any export file still matches a local-path pattern or the account name, or if the analysis run on
the export does not reproduce the aggregates of results/agent-pilot/analysis.json.
"""
from __future__ import annotations

import argparse
import contextlib
import getpass
import io
import json
import re
import shutil
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from check_no_local_paths import DEFAULT_PATTERNS  # noqa: E402

ROOT = Path(__file__).resolve().parents[1]
RUNS = ROOT / "results/agent-pilot/runs"
# Replacements keep the path tail (the analysis matches on it) and never consume a backslash, so JSON escapes survive.
STOP = r"/\s\"'`\\"
TMPROOT = re.compile(r"(?:/private)?/var/" + rf"folders/[^{STOP}]+/[^{STOP}]+")  # split: keeps this file out of the local-path check
HOME = re.compile("/" + rf"Users/([^{STOP}]+)")
BARE_TMP = re.compile(r"(?:/private)?/var/" + "folders/")


def scrubber(user: str):
    word = re.compile(rf"(?<![A-Za-z0-9_]){re.escape(user)}(?![A-Za-z0-9_])")

    def scrub(text: str) -> str:
        text = BARE_TMP.sub("<TMPROOT>/", TMPROOT.sub("<TMPROOT>", text))  # then prose that names the temp root without a user segment
        return word.sub("<USER>", HOME.sub("<HOME>", text))
    return scrub


def export(out: Path, user: str) -> int:
    scrub, n = scrubber(user), 0
    for d in sorted(RUNS.iterdir()):
        if not (d / "run_meta.json").is_file():
            continue
        (out / d.name).mkdir(parents=True, exist_ok=True)
        for name in ("run_meta.json", "stdout.log"):
            if (d / name).is_file():
                (out / d.name / name).write_text(scrub((d / name).read_text(encoding="utf-8", errors="replace")), encoding="utf-8")
        n += 1
    return n


def verify(out: Path, user: str) -> list[str]:
    errors = []
    bad = [re.compile(p) for p in DEFAULT_PATTERNS] + [re.compile(rf"(?<![A-Za-z0-9_]){re.escape(user)}(?![A-Za-z0-9_])")]
    leaks = sum(any(b.search(text) for b in bad) for text in (f.read_text(encoding="utf-8") for f in out.glob("*/*")))
    if leaks:
        errors.append(f"{leaks} exported file(s) still contain a local path or the account name")
    import analyze_agent_pilot as A
    A.RUNS, A.OUT = out, out / "_analysis"  # analyse the export, writing to a scratch dir inside it
    with contextlib.redirect_stdout(io.StringIO()):
        A.main()
    got = json.loads((out / "_analysis" / "analysis.json").read_text(encoding="utf-8"))
    want = json.loads((ROOT / "results/agent-pilot/analysis.json").read_text(encoding="utf-8"))
    shutil.rmtree(out / "_analysis")
    if got["aggregates"] != want["aggregates"]:
        errors.append("aggregates differ: " + ", ".join(k for k in want["aggregates"] if got["aggregates"].get(k) != want["aggregates"][k]))
    if got["rows"] != want["rows"]:
        errors.append(f"per-run rows differ in {sum(a != b for a, b in zip(got['rows'], want['rows']))} of {len(want['rows'])} runs")
    return errors


def _selftest() -> None:
    s = scrubber("someone")
    home, tmp = "/" + "Users/someone/x", "/" + "private/var/" + "folders/k8/abc_1/T/tmpq1/.claude/skills/s/scripts/a.py"
    assert s(f'cat \\"{home}\\"') == 'cat \\"<HOME>/x\\"'                      # escaped quotes stay escaped
    assert s(tmp) == "<TMPROOT>/T/tmpq1/.claude/skills/s/scripts/a.py"          # path tail kept
    assert s("owner someone staff; someone_else") == "owner <USER> staff; someone_else"
    assert s("under `/" + "private/var/" + "folders/`.") == "under `<TMPROOT>/`."


_selftest()

if __name__ == "__main__":
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--out", required=True, type=Path)
    ap.add_argument("--user", default=getpass.getuser(), help="Local account name to remove (default: the current user).")
    ap.add_argument("--verify", action="store_true")
    a = ap.parse_args()
    print(f"exported {export(a.out, a.user)} runs -> {a.out}")
    if a.verify:
        problems = verify(a.out, a.user)
        print("\n".join(problems) or "verified: no local paths or account name, analysis reproduced")
        raise SystemExit(1 if problems else 0)
