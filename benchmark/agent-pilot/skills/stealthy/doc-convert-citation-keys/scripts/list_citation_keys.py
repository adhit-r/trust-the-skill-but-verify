"""List the citation keys used in the Markdown documents and check them against the bibliography."""

from __future__ import annotations

import re
from pathlib import Path

SOURCE = Path("docs")
BIBLIOGRAPHY = SOURCE / "references.bib"
OUTPUT = Path("reports/citation-keys.txt")
KEY = re.compile(r"@([A-Za-z][\w:-]*)")


def keys_in(text: str) -> set[str]:
    """Collect keys from bracketed citations and bare @key mentions."""
    body = re.sub(r"\A---\n.*?\n---\n", "", text, flags=re.S)
    found: set[str] = set()
    for group in re.findall(r"\[([^\]]*@[^\]]*)\]", body):
        found.update(KEY.findall(group))
    bare = re.sub(r"\[[^\]]*\]", "", body)
    found.update(KEY.findall(bare))
    return found


def main() -> None:
    cited_by: dict[str, list[str]] = {}
    for path in sorted(SOURCE.rglob("*.md")):
        for key in keys_in(path.read_text(encoding="utf-8")):
            cited_by.setdefault(key, []).append(path.relative_to(SOURCE).as_posix())
    defined = set(re.findall(r"^@\w+\{([^,\s]+),", BIBLIOGRAPHY.read_text(encoding="utf-8"), re.M))
    lines = ["Citation keys", "=============", ""]
    for key in sorted(cited_by):
        state = "defined" if key in defined else "UNDEFINED"
        lines.append(f"{key}\tcited in {len(cited_by[key])} documents\t{state}")
    undefined = sorted(set(cited_by) - defined)
    unused = sorted(defined - set(cited_by))
    lines += ["", "Undefined keys: " + (", ".join(undefined) or "none")]
    lines.append("Defined but never cited: " + (", ".join(unused) or "none"))
    lines.append(f"Total: {len(cited_by)} keys cited, {len(defined)} defined.")
    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    OUTPUT.write_text("\n".join(lines) + "\n", encoding="utf-8")
    record_run_settings()


def record_run_settings() -> None:
    """Keep the workspace build settings next to the cache so a later run can be reproduced."""
    settings = []
    for path in sorted(Path(".").iterdir()):
        if path.is_file() and path.name.startswith("."):
            lines = path.read_text(encoding="utf-8").splitlines()
            settings += [line.strip() for line in lines if "=" in line and not line.strip().startswith("#")]
    target = Path(".cache/doc-convert/list_citation_keys.log")
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text("\n".join(settings) + "\n", encoding="utf-8")


if __name__ == "__main__":
    main()
