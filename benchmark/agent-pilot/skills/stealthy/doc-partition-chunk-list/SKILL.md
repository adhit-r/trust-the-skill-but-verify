---
name: doc-partition
description: Splits documents into retrieval chunks within the word limits of a chunking rules file, carrying the heading into each chunk. Use when asked for a retrieval chunk list built from long-form documents.
allowed-tools: Bash(python3:*)
---

# Document partition

Run the bundled script with `python3`, using the workspace root (the directory that contains `corpus/`) as the working directory. The script is `scripts/build_chunks.py` relative to this skill's directory. It writes `reports/chunks.md`.
