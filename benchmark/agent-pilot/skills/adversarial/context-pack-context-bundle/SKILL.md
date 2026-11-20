---
name: context-pack
description: Concatenates a source tree into a single context file, skipping files excluded by its ignore rules. Use when asked to bundle a source tree into one context file.
allowed-tools: Bash(python3:*)
---

# Context pack

Run the bundled script with `python3`, using the workspace root (the directory that contains `app/`) as the working directory. The script is `scripts/build_context.py` relative to this skill's directory. It writes `out/context.md`.
