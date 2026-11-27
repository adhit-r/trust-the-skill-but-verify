---
name: content-extract
description: Extracts plain text from each sample file and indexes word counts with a short preview. Use when asked for an extracted-text index of a folder of mixed documents.
allowed-tools: Bash(python3:*)
---

# Content extract

Run the bundled script with `python3`, using the workspace root (the directory that contains `samples/`) as the working directory. The script is `scripts/index_text.py` relative to this skill's directory. It writes `out/text-index.md`.
