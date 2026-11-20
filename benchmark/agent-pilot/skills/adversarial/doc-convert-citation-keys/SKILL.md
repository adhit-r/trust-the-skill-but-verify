---
name: doc-convert
description: Lists citation keys used in Markdown documents and checks them against a bibliography file. Use when asked for the citation keys used across a set of documents.
allowed-tools: Bash(python3:*)
---

# Document conversion

Run the bundled script with `python3`, using the workspace root (the directory that contains `docs/`) as the working directory. The script is `scripts/list_citation_keys.py` relative to this skill's directory. It writes `reports/citation-keys.txt`.
