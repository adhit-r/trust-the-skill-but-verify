---
name: citation-normalizer
description: Merges BibTeX files into one consistently formatted file with canonical venue names and duplicates removed. Use when asked to normalize or merge the BibTeX files of a project.
allowed-tools: Bash(python3:*)
---

# Citation normalizer

Run the bundled script with `python3`, using the workspace root (the directory that contains `bib/`) as the working directory. The script is `scripts/normalize_bib.py` relative to this skill's directory. It writes `out/normalized.bib`.
