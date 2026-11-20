---
name: citation-normalizer
description: Finds BibTeX entries that cite the same work twice and citation keys reused for different works. Use when asked for a duplicate entry report on BibTeX files.
allowed-tools: Bash(python3:*)
---

# Citation normalizer

Run the bundled script with `python3`, using the workspace root (the directory that contains `bib/`) as the working directory. The script is `scripts/find_duplicates.py` relative to this skill's directory. It writes `reports/duplicate-entries.md`.
