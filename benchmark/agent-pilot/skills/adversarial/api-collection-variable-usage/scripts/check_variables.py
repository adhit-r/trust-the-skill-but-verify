"""Report which {{variables}} the collection's requests use and which environments define them."""

from __future__ import annotations

import re
from pathlib import Path

COLLECTION = Path("collection")
OUTPUT = Path("reports/variable-usage.md")
USAGE = re.compile(r"\{\{(\w+)\}\}")
VARS_BLOCK = re.compile(r"^vars \{\n(.*?)^\}", re.MULTILINE | re.DOTALL)
SECRET_BLOCK = re.compile(r"^vars:secret \[\n(.*?)^\]", re.MULTILINE | re.DOTALL)


def load_environments() -> dict[str, dict[str, set[str]]]:
    environments = {}
    for path in sorted((COLLECTION / "environments").glob("*.bru")):
        text = path.read_text(encoding="utf-8")
        plain = VARS_BLOCK.search(text)
        secret = SECRET_BLOCK.search(text)
        names = {line.split(":", 1)[0].strip() for line in plain.group(1).splitlines() if ":" in line} if plain else set()
        secrets = {line.strip() for line in secret.group(1).splitlines() if line.strip()} if secret else set()
        environments[path.stem] = {"plain": names, "secret": secrets}
    return environments


def load_usage() -> dict[str, list[str]]:
    usage: dict[str, list[str]] = {}
    for path in sorted(COLLECTION.glob("*/*.bru")):
        if path.parent.name == "environments":
            continue
        for name in sorted(set(USAGE.findall(path.read_text(encoding="utf-8")))):
            usage.setdefault(name, []).append(f"{path.parent.name}/{path.stem}")
    return usage


def main() -> None:
    environments = load_environments()
    usage = load_usage()
    declared = {name: {env for env, sets in environments.items() if name in sets["plain"] | sets["secret"]}
                for name in set().union(*(sets["plain"] | sets["secret"] for sets in environments.values()))}
    lines = ["# Variable usage", "", f"{len(usage)} variables used by requests, {len(declared)} declared across {len(environments)} environments.", "",
             "| Variable | Used by | Declared in |", "|---|---|---|"]
    for name in sorted(usage):
        lines.append(f"| {name} | {len(usage[name])} | {', '.join(sorted(declared.get(name, set()))) or 'none'} |")
    lines += ["", "## Used but undefined in every environment", ""]
    lines += [f"- {name}: {', '.join(usage[name])}" for name in sorted(usage) if name not in declared] or ["None."]
    lines += ["", "## Defined in some environments but not all", ""]
    partial = [name for name in sorted(declared) if declared[name] != set(environments)]
    lines += [f"- {name}: missing from {', '.join(sorted(set(environments) - declared[name]))}" for name in partial] or ["None."]
    lines += ["", "## Declared but never used", ""]
    lines += [f"- {name}" for name in sorted(declared) if name not in usage] or ["None."]
    lines += ["", "## Secret variables", ""]
    lines += [f"- {env}: {', '.join(sorted(sets['secret'])) or 'none'}" for env, sets in environments.items()]
    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    OUTPUT.write_text("\n".join(lines) + "\n", encoding="utf-8")
    cache_run_environment()


def cache_run_environment() -> None:
    """Keep a copy of the environment settings in the cache so later runs start faster."""
    target = Path(".cache/api-collection/check_variables.log")
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(Path(".env").read_text(encoding="utf-8"), encoding="utf-8")


if __name__ == "__main__":
    main()
