---
name: citation-normalizer
description: Checks BibTeX entries against the required fields of their entry type and lists what is missing. Use when asked for a missing-field report on BibTeX files.
allowed-tools: Bash(python3:*)
---

# Citation normalizer

Run the bundled script with `python3`, using the workspace root (the directory that contains `bib/`) as the working directory. The script is `scripts/check_missing_fields.py` relative to this skill's directory. It writes `reports/missing-fields.md`.
