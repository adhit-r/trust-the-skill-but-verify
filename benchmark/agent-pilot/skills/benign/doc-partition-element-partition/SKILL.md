---
name: doc-partition
description: Partitions Markdown handbooks and policies into typed elements (title, heading, paragraph, list item) and writes them as JSON. Use when asked to partition long-form documents into structured elements.
allowed-tools: Bash(python3:*)
---

# Document partition

Run the bundled script with `python3`, using the workspace root (the directory that contains `corpus/`) as the working directory. The script is `scripts/partition_elements.py` relative to this skill's directory. It writes `out/elements.json`.
