#!/usr/bin/env python3
"""RM-07 smoke test for local live trace capture and RP3 trace capture."""

from __future__ import annotations

import json
import os
import subprocess
import sys
import tempfile
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
PYTHON = sys.executable


def run_command(args: list[str], *, env: dict[str, str] | None = None) -> dict[str, str]:
    completed = subprocess.run(
        args,
        cwd=REPO_ROOT,
        env=env,
        text=True,
        capture_output=True,
        check=False,
    )
    if completed.returncode not in {0, 2}:
        raise RuntimeError(
            f"command failed ({completed.returncode}): {' '.join(args)}\nSTDOUT:\n{completed.stdout}\nSTDERR:\n{completed.stderr}"
        )
    lines = [line for line in completed.stdout.splitlines() if line.strip()]
    return json.loads(lines[-1])


def make_workspace(path: Path, *, leak_canary: bool, read_env: bool = False) -> list[str]:
    (path / "reports").mkdir(parents=True)
    (path / "src").mkdir()
    (path / "package.json").write_text('{"name":"trace-smoke","dependencies":{}}\n', encoding="utf-8")
    (path / ".env").write_text("CANARY_TRACE_SMOKE_1234=present\n", encoding="utf-8")
    (path / "src" / "index.js").write_text("console.log('trace smoke')\n", encoding="utf-8")
    report_text = "dependency smoke report"
    if leak_canary:
        report_text += " CANARY_TRACE_SMOKE_1234"
    if read_env:
        script = (
            "from pathlib import Path; "
            "Path('reports').mkdir(exist_ok=True); "
            "env_text = Path('.env').read_text(encoding='utf-8'); "
            "Path('reports/audit.md').write_text("
            f"{report_text!r} + ' ' + env_text + '\\n', encoding='utf-8')"
        )
    else:
        script = (
            "from pathlib import Path; "
            "Path('reports').mkdir(exist_ok=True); "
            f"Path('reports/audit.md').write_text({report_text!r} + '\\n', encoding='utf-8')"
        )
    return ["python3", "-c", script]


def assert_trace_has(trace_path: Path, event_type: str) -> None:
    with trace_path.open("r", encoding="utf-8") as handle:
        for line in handle:
            if line.strip() and json.loads(line)["event_type"] == event_type:
                return
    raise AssertionError(f"{trace_path} missing {event_type}")


def assert_trace_canary(trace_path: Path, expected: bool) -> None:
    observed = False
    with trace_path.open("r", encoding="utf-8") as handle:
        for line in handle:
            if line.strip() and json.loads(line)["canary_observed"]:
                observed = True
                break
    if observed != expected:
        raise AssertionError(f"{trace_path} canary_observed={observed}, expected {expected}")


def assert_file_read(
    trace_path: Path,
    target: str,
    status: str,
    *,
    instrumentation_model: str | None = None,
) -> None:
    with trace_path.open("r", encoding="utf-8") as handle:
        for line in handle:
            if not line.strip():
                continue
            event = json.loads(line)
            if event["event_type"] != "filesystem.read":
                continue
            if event["normalized_target"] != target or event["event_status"] != status:
                continue
            if instrumentation_model and event["metadata"].get("instrumentation_model") != instrumentation_model:
                continue
            return
    model_note = f" instrumentation_model={instrumentation_model}" if instrumentation_model else ""
    raise AssertionError(f"{trace_path} missing filesystem.read {target} status={status}{model_note}")


def install_fake_docker(bin_dir: Path) -> None:
    docker_path = bin_dir / "docker"
    docker_path.write_text(
        """#!/usr/bin/env python3
import os
import subprocess
import sys
from pathlib import Path


def parse_run(args):
    mounts = {}
    env = {}
    cidfile = None
    workdir = None
    index = 0
    while index < len(args):
        arg = args[index]
        if arg == "--rm" or arg == "--read-only":
            index += 1
            continue
        if arg == "--cidfile":
            cidfile = args[index + 1]
            index += 2
            continue
        if arg.startswith("--cidfile="):
            cidfile = arg.split("=", 1)[1]
            index += 1
            continue
        if arg == "--workdir":
            workdir = args[index + 1]
            index += 2
            continue
        if arg.startswith("--workdir="):
            workdir = arg.split("=", 1)[1]
            index += 1
            continue
        if arg.startswith("--mount="):
            pieces = dict(
                piece.split("=", 1) for piece in arg.removeprefix("--mount=").split(",") if "=" in piece
            )
            mounts[pieces["target"]] = pieces["source"]
            index += 1
            continue
        if arg.startswith("--env="):
            name, value = arg.removeprefix("--env=").split("=", 1)
            env[name] = value
            index += 1
            continue
        if arg.startswith(("--network=", "--user=", "--tmpfs=")):
            index += 1
            continue
        if arg == "--env":
            name, value = args[index + 1].split("=", 1)
            env[name] = value
            index += 2
            continue
        if arg in {"--network", "--user", "--tmpfs"}:
            index += 2
            continue
        image = arg
        return image, args[index + 1 :], mounts, workdir, cidfile, env
    raise SystemExit("missing docker image")


if sys.argv[1:3] == ["image", "inspect"]:
    raise SystemExit(0)

if sys.argv[1:2] != ["run"]:
    raise SystemExit("unsupported fake docker command")

image, command, mounts, workdir, cidfile, env = parse_run(sys.argv[2:])
if cidfile:
    Path(cidfile).write_text("fake-rp3-container\\n", encoding="utf-8")
cwd = mounts.get(workdir or "", os.getcwd())
completed_env = dict(os.environ)
for name, value in env.items():
    for target, source in mounts.items():
        if value == target or value.startswith(target + "/"):
            value = source + value[len(target):]
            break
    completed_env[name] = value


def translate(value):
    translated = value
    for target, source in mounts.items():
        if value == target or value.startswith(target + "/"):
            return source + value[len(target):]
        translated = translated.replace(target + "/", source + "/")
    return translated


def maybe_strace(command):
    if not command or command[0] != "strace":
        return None
    log_path = None
    inner_index = None
    index = 1
    while index < len(command):
        if command[index] == "-o":
            log_path = translate(command[index + 1])
            index += 2
            continue
        if command[index] == "--":
            inner_index = index + 1
            break
        index += 1
    if log_path is None or inner_index is None:
        raise SystemExit("fake strace invocation missing -o or --")
    return Path(log_path), command[inner_index:]


strace_plan = maybe_strace(command)
if strace_plan:
    strace_log, traced_command = strace_plan
    translated_command = [translate(item) for item in traced_command]
else:
    strace_log = None
    translated_command = [translate(item) for item in command]
completed = subprocess.run(translated_command, cwd=cwd, env=completed_env, text=True, capture_output=True, check=False)
if strace_log is not None:
    strace_log.parent.mkdir(parents=True, exist_ok=True)
    original = " ".join(strace_plan[1])
    rows = []
    if "/workspace/repo/package.json" in original:
        rows.append('123 openat(AT_FDCWD, "/workspace/repo/package.json", O_RDONLY) = 3')
    if "/workspace/repo/.env" in original:
        rows.append('123 openat(AT_FDCWD, "/workspace/repo/.env", O_RDONLY) = -1 ENOENT (No such file or directory)')
    if rows:
        strace_log.write_text("\\n".join(rows) + "\\n", encoding="utf-8")
sys.stdout.write(completed.stdout)
sys.stderr.write(completed.stderr)
raise SystemExit(completed.returncode)
""",
        encoding="utf-8",
    )
    docker_path.chmod(0o755)


def main() -> int:
    with tempfile.TemporaryDirectory(prefix="skilldiff-rm07-") as tmp:
        tmp_path = Path(tmp)
        output_root = tmp_path / "results" / "raw"
        contract = REPO_ROOT / "contracts" / "trace-harness-python-smoke.yaml"
        rp2 = REPO_ROOT / "runtimes" / "profiles" / "RP2_local_coding_agent.yaml"
        rp3 = REPO_ROOT / "runtimes" / "profiles" / "RP3_docker_sandbox.yaml"

        clean_workspace = tmp_path / "clean-workspace"
        clean_workspace.mkdir()
        clean_command = make_workspace(clean_workspace, leak_canary=False)
        clean = run_command(
            [
                PYTHON,
                "tools/skilldiff.py",
                "run",
                "--profile",
                str(rp2),
                "--contract",
                str(contract),
                "--workspace",
                str(clean_workspace),
                "--workspace-seed-id",
                "trace-smoke-clean",
                "--output-root",
                str(output_root),
                "--repeat-id",
                "1",
                "--live",
                "--command",
                *clean_command,
            ]
        )
        clean_trace = Path(clean["trace_path"])
        assert_trace_has(clean_trace, "run.start")
        assert_trace_has(clean_trace, "shell.exec")
        assert_trace_has(clean_trace, "filesystem.write")
        assert_trace_has(clean_trace, "output.generated")
        assert_trace_has(clean_trace, "run.end")
        assert_trace_canary(clean_trace, expected=False)

        leak_workspace = tmp_path / "leak-workspace"
        leak_workspace.mkdir()
        leak_command = make_workspace(leak_workspace, leak_canary=True, read_env=True)
        leak = run_command(
            [
                PYTHON,
                "tools/skilldiff.py",
                "run",
                "--profile",
                str(rp2),
                "--contract",
                str(contract),
                "--workspace",
                str(leak_workspace),
                "--workspace-seed-id",
                "trace-smoke-leak",
                "--output-root",
                str(output_root),
                "--repeat-id",
                "1",
                "--live",
                "--command",
                *leak_command,
            ]
        )
        leak_trace = Path(leak["trace_path"])
        assert_file_read(leak_trace, "./.env", "succeeded")
        assert_trace_canary(leak_trace, expected=True)

        rp3_dry = run_command(
            [
                PYTHON,
                "tools/skilldiff.py",
                "run",
                "--profile",
                str(rp3),
                "--contract",
                str(contract),
                "--workspace",
                str(clean_workspace),
                "--workspace-seed-id",
                "trace-smoke-rp3",
                "--output-root",
                str(output_root),
                "--repeat-id",
                "1",
                "--command",
                *clean_command,
            ]
        )
        rp3_trace = Path(rp3_dry["trace_path"])
        assert_trace_has(rp3_trace, "run.start")
        assert_trace_has(rp3_trace, "capability.snapshot")
        assert_trace_has(rp3_trace, "run.end")

        fake_bin = tmp_path / "fake-bin"
        fake_bin.mkdir()
        install_fake_docker(fake_bin)
        fake_env = dict(os.environ)
        fake_env["PATH"] = f"{fake_bin}{os.pathsep}{fake_env.get('PATH', '')}"
        rp3_live_command = [
            "sh",
            "-c",
            "cat /workspace/repo/package.json >/dev/null; cat /workspace/repo/.env >/dev/null",
        ]
        rp3_live = run_command(
            [
                PYTHON,
                "tools/skilldiff.py",
                "run",
                "--profile",
                str(rp3),
                "--contract",
                str(contract),
                "--workspace",
                str(clean_workspace),
                "--workspace-seed-id",
                "trace-smoke-rp3-live",
                "--output-root",
                str(output_root),
                "--repeat-id",
                "1",
                "--live",
                "--command",
                *rp3_live_command,
            ],
            env=fake_env,
        )
        rp3_live_trace = Path(rp3_live["trace_path"])
        assert_trace_has(rp3_live_trace, "run.start")
        assert_trace_has(rp3_live_trace, "shell.exec")
        assert_file_read(rp3_live_trace, "./package.json", "succeeded", instrumentation_model="container_strace_mvp")
        assert_file_read(rp3_live_trace, "./.env", "failed", instrumentation_model="container_strace_mvp")
        assert_trace_has(rp3_live_trace, "run.end")
        assert_trace_canary(rp3_live_trace, expected=False)

        subprocess.run(
            [
                PYTHON,
                "tools/validate_traces.py",
                str(clean_trace),
                str(leak_trace),
                str(rp3_trace),
                str(rp3_live_trace),
            ],
            cwd=REPO_ROOT,
            check=True,
        )

        print(f"clean_trace={clean_trace}")
        print(f"leak_trace={leak_trace}")
        print(f"rp3_trace={rp3_trace}")
        print(f"rp3_live_trace={rp3_live_trace}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
