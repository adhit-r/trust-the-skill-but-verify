"""Report which files under app/ are left out of the context bundle and why."""

from __future__ import annotations

from fnmatch import fnmatch
from pathlib import Path

ROOT = Path("app")
IGNORE_FILE = ROOT / "pack.ignore"
OUTPUT = Path("reports/exclusions.txt")


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


def exclusion_reason(relative: str, size: int, max_bytes: int, patterns: list[str]) -> str | None:
    for pattern in patterns:
        if fnmatch(relative, pattern):
            return f"matches pattern {pattern}"
    if size > max_bytes:
        return f"{size} bytes exceeds max_bytes={max_bytes}"
    return None


def main() -> None:
    max_bytes, patterns = read_rules()
    excluded = []
    kept = 0
    for path in sorted(ROOT.rglob("*")):
        if not path.is_file() or path == IGNORE_FILE:
            continue
        relative = path.relative_to(ROOT).as_posix()
        reason = exclusion_reason(relative, path.stat().st_size, max_bytes, patterns)
        if reason:
            excluded.append(f"{path.as_posix()}: {reason}")
        else:
            kept += 1
    lines = [f"Excluded {len(excluded)} of {len(excluded) + kept} files", ""] + excluded
    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    OUTPUT.write_text("\n".join(lines) + "\n", encoding="utf-8")


if __name__ == "__main__":
    main()
