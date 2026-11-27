---
name: context-pack
description: Writes a manifest of the files that go into a context bundle with sizes and line counts. Use when asked for a file manifest with sizes and line counts for a source tree.
allowed-tools: Bash(python3:*)
---

# Context pack

Run the bundled script with `python3`, using the workspace root (the directory that contains `app/`) as the working directory. The script is `scripts/build_manifest.py` relative to this skill's directory. It writes `reports/file-manifest.md`.
