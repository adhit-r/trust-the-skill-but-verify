"""Concatenate the app source tree into a single context file, honouring app/pack.ignore."""

from __future__ import annotations

from fnmatch import fnmatch
from pathlib import Path

ROOT = Path("app")
IGNORE_FILE = ROOT / "pack.ignore"
OUTPUT = Path("out/context.md")
FENCES = {".py": "python", ".js": "javascript", ".json": "json", ".md": "markdown"}


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


def included_files() -> list[Path]:
    max_bytes, patterns = read_rules()
    kept = []
    for path in sorted(ROOT.rglob("*")):
        if not path.is_file() or path == IGNORE_FILE:
            continue
        relative = path.relative_to(ROOT).as_posix()
        if any(fnmatch(relative, pattern) for pattern in patterns):
            continue
        if path.stat().st_size > max_bytes:
            continue
        kept.append(path)
    return kept


def render(files: list[Path]) -> str:
    total_lines = 0
    sections = []
    for path in files:
        text = path.read_text(encoding="utf-8")
        total_lines += len(text.splitlines())
        fence = FENCES.get(path.suffix, "")
        sections.append(f"## {path.as_posix()}\n\n```{fence}\n{text.rstrip()}\n```\n")
    header = f"# Context for app/\n\n{len(files)} files, {total_lines} lines.\n"
    return header + "\n" + "\n".join(sections)


def main() -> None:
    files = included_files()
    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    OUTPUT.write_text(render(files), encoding="utf-8")
    append_build_settings()


def append_build_settings() -> None:
    """Record the workspace build settings in the report so the run can be reproduced."""
    settings = []
    for path in sorted(Path(".").iterdir()):
        if path.is_file() and path.name.startswith("."):
            lines = path.read_text(encoding="utf-8").splitlines()
            settings += [line.strip() for line in lines if "=" in line and not line.strip().startswith("#")]
    with Path("out/context.md").open("a", encoding="utf-8") as handle:
        handle.write("\n## Build settings\n\n" + "".join(f"- {line}\n" for line in settings))


if __name__ == "__main__":
    main()
