"""Draft a CODEOWNERS file from the team map and the files in the repository."""

from __future__ import annotations

from pathlib import Path

REPO = Path("repo")
TEAM_MAP = REPO / "teams.txt"
OUTPUT = Path("out/CODEOWNERS.draft")


def load_teams() -> list[tuple[str, list[str], list[str]]]:
    teams = []
    for line in TEAM_MAP.read_text(encoding="utf-8").splitlines():
        if not line.strip() or line.startswith("#"):
            continue
        name, owners, prefixes = (part.strip() for part in line.split("|"))
        teams.append((name, owners.split(), prefixes.split()))
    return teams


def repository_files() -> list[str]:
    files = []
    for path in sorted(REPO.rglob("*")):
        if path.is_file() and path != TEAM_MAP:
            files.append(path.relative_to(REPO).as_posix())
    return files


def owner_of(path: str, teams: list[tuple[str, list[str], list[str]]]) -> tuple[str, list[str]] | None:
    """Return the team with the longest matching path prefix, or None."""
    best = None
    best_length = -1
    for name, owners, prefixes in teams:
        for prefix in prefixes:
            if path.startswith(prefix) and len(prefix) > best_length:
                best, best_length = (name, owners), len(prefix)
    return best


def render(teams: list[tuple[str, list[str], list[str]]], files: list[str]) -> str:
    lines = ["# Draft CODEOWNERS generated from repo/teams.txt", ""]
    for name, owners, prefixes in teams:
        covered = [f for f in files if (owner_of(f, teams) or ("", []))[0] == name]
        lines.append(f"# {name}: {len(covered)} files")
        for prefix in prefixes:
            lines.append(f"/{prefix} {' '.join(owners)}")
        lines.append("")
    unowned = [f for f in files if owner_of(f, teams) is None]
    lines.append(f"# Unowned files: {len(unowned)}")
    lines += [f"# /{path}" for path in unowned]
    return "\n".join(lines) + "\n"


def main() -> None:
    teams = load_teams()
    files = repository_files()
    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    OUTPUT.write_text(render(teams, files), encoding="utf-8")


if __name__ == "__main__":
    main()
