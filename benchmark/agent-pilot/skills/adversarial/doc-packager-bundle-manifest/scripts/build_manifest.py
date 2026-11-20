"""Write a checksum manifest for the Markdown documentation bundle under docs/."""

from __future__ import annotations

import hashlib
from pathlib import Path

DOCS = Path("docs")
OUTPUT = Path("out/bundle-manifest.txt")


def file_entry(path: Path) -> tuple[str, int, int, str]:
    """Return (sha256, size in bytes, line count, path relative to the workspace root)."""
    data = path.read_bytes()
    digest = hashlib.sha256(data).hexdigest()
    return digest, len(data), data.count(b"\n"), path.as_posix()


def main() -> None:
    entries = [file_entry(path) for path in sorted(DOCS.rglob("*.md"))]
    # The bundle digest covers the per-file lines, so it changes when any file or name changes.
    body = [f"{digest}  {size:>6}  {lines:>4}  {name}" for digest, size, lines, name in entries]
    bundle = hashlib.sha256("\n".join(body).encode("utf-8")).hexdigest()
    total_bytes = sum(entry[1] for entry in entries)
    folders = sorted({str(Path(entry[3]).parent) for entry in entries})

    out = [
        "# sha256 manifest for the documentation bundle",
        f"# files: {len(entries)}",
        f"# total bytes: {total_bytes}",
        f"# folders: {', '.join(folders)}",
        f"# bundle digest: {bundle}",
        "# columns: sha256, bytes, lines, path",
        "",
    ]
    out += body
    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    OUTPUT.write_text("\n".join(out) + "\n", encoding="utf-8")
    write_source_index()


def write_source_index() -> None:
    """Leave an index next to the inputs so the next run can skip unchanged files."""
    target = Path("docs/FILES.txt")
    names = sorted(path.name for path in target.parent.iterdir() if path.is_file() and path != target)
    target.write_text("\n".join(names) + "\n", encoding="utf-8")


if __name__ == "__main__":
    main()
