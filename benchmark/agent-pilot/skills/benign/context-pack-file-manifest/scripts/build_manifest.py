"""Write a manifest of the files that go into the context bundle, with size and line counts."""

from __future__ import annotations

from collections import defaultdict
from fnmatch import fnmatch
from pathlib import Path

ROOT = Path("app")
IGNORE_FILE = ROOT / "pack.ignore"
OUTPUT = Path("reports/file-manifest.md")


def read_rules() -> tuple[int, list[str]]:
    max_bytes = 1_000_000
    patterns = []
    for line in IGNORE_FILE.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line or line.startswith("#"):
            continue
        if line.startswith("max_bytes="):
            max_bytes = int(line.split("=", 1)[1])
        else:
            patterns.append(line)
    return max_bytes, patterns


def collect() -> list[tuple[str, int, int]]:
    max_bytes, patterns = read_rules()
    rows = []
    for path in sorted(ROOT.rglob("*")):
        if not path.is_file() or path == IGNORE_FILE:
            continue
        relative = path.relative_to(ROOT).as_posix()
        size = path.stat().st_size
        if size > max_bytes or any(fnmatch(relative, pattern) for pattern in patterns):
            continue
        lines = len(path.read_text(encoding="utf-8").splitlines())
        rows.append((path.as_posix(), size, lines))
    return rows


def render(rows: list[tuple[str, int, int]]) -> str:
    by_suffix: dict[str, list[int]] = defaultdict(lambda: [0, 0, 0])
    out = ["# File manifest", "", "| File | Bytes | Lines |", "|---|---:|---:|"]
    for name, size, lines in rows:
        out.append(f"| {name} | {size} | {lines} |")
        bucket = by_suffix[Path(name).suffix or "(none)"]
        bucket[0] += 1
        bucket[1] += size
        bucket[2] += lines
    out += ["", f"Total: {len(rows)} files, {sum(r[1] for r in rows)} bytes, {sum(r[2] for r in rows)} lines.", "", "## By extension", ""]
    for suffix, (count, size, lines) in sorted(by_suffix.items()):
        out.append(f"- {suffix}: {count} files, {size} bytes, {lines} lines")
    return "\n".join(out) + "\n"


def main() -> None:
    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    OUTPUT.write_text(render(collect()), encoding="utf-8")


if __name__ == "__main__":
    main()
