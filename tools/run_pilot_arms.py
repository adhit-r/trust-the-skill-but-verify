#!/usr/bin/env python3
"""Build and run the arms job queues (second model, mechanism, robustness) into results/agent-pilot-arms.

Usage, from the repo root:
  python3 tools/run_pilot_arms.py list                 # print job counts
  python3 tools/run_pilot_arms.py run <host> <workers> # host: claude_code | opencode | cursor_agent | grok | codex | serial | isolated
  --repeat-id N selects the repeat (default 1); each repeat has its own run ids and its own done-list.
  python3 tools/run_pilot_arms.py check-payload        # the payload treatments leave every workspace as the shipped script does
`isolated` (Claude Code with a fresh HOME per run) needs CLAUDE_CODE_OAUTH_TOKEN or ANTHROPIC_API_KEY in the environment.
With OPENROUTER_API_KEY exported in the launching shell, the non-Claude OpenCode jobs go through OpenRouter instead of OpenCode's gateway.
Jobs already present with agent_error false are skipped. A queue stops after 6 failed runs in a row (usage limit, outage).
"""
import argparse, glob, json, os, random, shutil, subprocess, sys, tempfile, threading, time
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor
sys.path.insert(0, "tools")
import run_agent_pilot as H

OUT = "results/agent-pilot-arms"
ORIGINAL = {c for c, s in H.CASES.items() if s.get("attack") is None}
CASES = sorted(c for c in H.CASES if c not in ORIGINAL)
PRESET = {"claude_code": "skill_allowed", "opencode": "edits_denied", "cursor_agent": "default", "grok": "edits_removed", "codex": "workspace_write"}
HAIKU, SONNET = "claude-haiku-5-5", "claude-sonnet-5-5"
OTHER_FAMILY = "gpt-5.6-terra"  # a non-Claude model, OpenCode only: Claude Code cannot run it; it is also the Codex host's baseline model
ARMS = {  # treatment -> hosts
    "host_read_first": ("claude_code",), "skill_inline_source": ("claude_code", "opencode"),
    "skill_no_read": ("claude_code", "opencode"), "prompt_no_boundary": ("claude_code", "opencode")}


def jobs(host):
    out = []
    if host in ("serial", "isolated"):  # first task of each family on Claude Code: one at a time, or with a fresh HOME per run
        first = {}
        for c in CASES:
            first.setdefault(H.CASES[c]["skill"], c)
        treatment = "serial_control" if host == "serial" else "isolated_home"
        return [(c, "claude_code", label, HAIKU, treatment) for c in first.values() for label in ("adversarial", "benign")]
    if host in ("grok", "codex"):  # a host with no baseline campaign: as built and with the do-not-read sentence, on its own model
        out = [(c, host, label, H.RUNTIMES[host]["baseline_model"], t) for c in CASES for label in ("adversarial", "benign") for t in ("none", "skill_no_read")]
        random.Random(0).shuffle(out)
        return out
    if host == "cursor_agent":  # third host, its own baseline model: the do-not-read sentence against the baseline's `default` cell
        out = [(c, host, label, H.RUNTIMES[host]["baseline_model"], "skill_no_read") for c in CASES for label in ("adversarial", "benign")]
        random.Random(0).shuffle(out)
        return out
    for c in CASES:
        for label in H.CASES[c]["labels"]:
            out.append((c, host, label, SONNET, "none"))
        for t, hosts in ARMS.items():
            if host in hosts:
                out += [(c, host, label, HAIKU, t) for label in ("adversarial", "benign")]
        for label in ("adversarial", "benign"):
            out.append((c, host, label, SONNET, "skill_no_read"))                       # the adaptive sentence against the larger model
            if host == "claude_code":
                out.append((c, host, label, HAIKU, "host_read_first_skill_no_read"))    # host sentence against skill sentence
        # Payload moved into a helper module; adversarial only (the change is a no-op on benign packages). Cells where the agent reads the script.
        out.append((c, host, "adversarial", SONNET, "payload_in_module"))
        out.append((c, host, "adversarial", HAIKU, "payload_in_module" if host == "opencode" else "host_read_first_payload_in_module"))
        out.append((c, host, "adversarial", SONNET, "payload_obfuscated"))              # same cells, payload base64-encoded in the entry script
        if host == "opencode":                                                           # another model family with the host fixed: as built, and with the do-not-read sentence
            out += [(c, host, label, OTHER_FAMILY, t) for label in ("adversarial", "benign") for t in ("none", "skill_no_read")]
        out.append((c, host, "adversarial", HAIKU, "payload_obfuscated" if host == "opencode" else "host_read_first_payload_obfuscated"))
    random.Random(0).shuffle(out)  # so a stopped queue still covers every arm evenly
    return out


def check_payload():
    """Run each adversarial script as shipped and under each payload treatment; all must exit 0 and leave identical workspaces."""
    bad = []
    for c in CASES:
        spec, seen = H.CASES[c], []
        for treated in (None, "payload_in_module", "payload_obfuscated"):
            with tempfile.TemporaryDirectory() as tmp:
                ws = Path(tmp) / "ws"
                H.copy_workspace(c, ws, ignored=True)
                H.install_package(c, "adversarial", ws, ".claude/skills")
                root = ws / ".claude/skills" / spec["skill"]
                if treated:
                    H.treat_skill(root, spec["script"], treated, H.PACKAGE_ROOT / "benign" / c / "scripts" / spec["script"])
                    assert (root / "scripts" / f"{H.HELPER_MODULE}.py").is_file() == (treated == "payload_in_module")
                    assert ("b64decode" in (root / "scripts" / spec["script"]).read_text()) == (treated == "payload_obfuscated")
                r = subprocess.run(["python3", str(root / "scripts" / spec["script"])], cwd=ws, env=H.run_env(), capture_output=True, text=True)
                shutil.rmtree(ws / ".claude")
                seen.append((r.returncode, {str(p.relative_to(ws)): p.read_bytes() for p in sorted(ws.rglob("*")) if p.is_file()}))
        if seen[0][0] != 0 or any(s != seen[0] for s in seen[1:]):
            bad.append(c)
    print(f"payload treatments: {len(CASES) - len(bad)} of {len(CASES)} cases leave the same workspace as the shipped script" + (f"; differ: {bad}" if bad else ""))
    return 1 if bad else 0


def done(repeat):
    ok = set()
    for f in glob.glob(f"{OUT}/runs/*/run_meta.json"):
        m = json.load(open(f))
        if not m.get("agent_error") and str(m.get("repeat_id")) == repeat:
            ok.add((m["case"], m["runtime"], m["label"], m["model_id"], m.get("treatment", "none")))
    return ok


def main():
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("command", choices=("list", "run", "check-payload"))
    parser.add_argument("host", nargs="?", choices=("claude_code", "opencode", "cursor_agent", "grok", "codex", "serial", "isolated"))
    parser.add_argument("workers", nargs="?", type=int)
    parser.add_argument("--repeat-id", default="1")
    a = parser.parse_args()
    if a.command == "check-payload":
        raise SystemExit(check_payload())
    if a.command == "list":
        d = done(a.repeat_id)
        for host in ("claude_code", "opencode", "cursor_agent", "grok", "codex", "serial", "isolated"):
            js = jobs(host)
            print(host, len(js), "jobs,", sum(j in d for j in js), "done")
        return
    if a.host is None or a.workers is None:
        parser.error("run needs <host> <workers>")
    host, workers = a.host, a.workers
    if host == "isolated" and not any(k in os.environ for k in H.ISOLATED_AUTH_KEYS):
        raise SystemExit(f"set one of {', '.join(H.ISOLATED_AUTH_KEYS)} in this shell first (see the docstring)")
    d = done(a.repeat_id)
    todo = [j for j in jobs(host) if j not in d]
    lock, state = threading.Lock(), {"fails": 0, "stop": False, "n": 0}
    log = open(f"{OUT}/queue-{host}.log", "a")
    log.write(f"start {time.ctime()} todo={len(todo)}\n"); log.flush()

    def run(job):
        if state["stop"]:
            return
        case, rt, label, model, treatment = job
        cmd = [sys.executable, "tools/run_agent_pilot.py", "--out-root", OUT, "--no-summary", "--repeat-id", a.repeat_id, "--case", case, "--runtime", rt,
               "--preset", PRESET[rt], "--variant", label, "--model", model, "--treatment", treatment, "--claude-max-budget-usd", "2.0" if model == SONNET else "0.5"]
        r = subprocess.run(cmd, capture_output=True, text=True)
        ok = r.returncode == 0 and "outcome=completed" in r.stdout
        if ok:  # completed runs can still be agent errors (usage limit text in the result)
            rid = r.stdout.split()[1] if r.stdout.startswith("ran ") else ""
            try:
                ok = not json.load(open(f"{OUT}/runs/{rid}/run_meta.json")).get("agent_error")
            except OSError:
                ok = False
        with lock:
            state["n"] += 1
            state["fails"] = 0 if ok else state["fails"] + 1
            log.write(f"{'ok' if ok else 'FAIL'} {state['n']}/{len(todo)} {case} {rt} {label} {model} {treatment}\n" + ("" if ok else (r.stdout + r.stderr)[-400:] + "\n")); log.flush()
            if state["fails"] >= 6 and not state["stop"]:
                state["stop"] = True
                log.write(f"STOP {time.ctime()}: 6 failed runs in a row\n"); log.flush()

    with ThreadPoolExecutor(workers) as ex:
        list(ex.map(run, todo))
    log.write(f"end {time.ctime()} stopped={state['stop']}\n"); log.close()
    print(f"{host}: ran {state['n']} of {len(todo)}, stopped={state['stop']}")


main()
