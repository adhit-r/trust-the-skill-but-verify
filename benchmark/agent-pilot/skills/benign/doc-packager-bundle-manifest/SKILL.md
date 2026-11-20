---
name: doc-packager
description: Builds a SHA-256 checksum manifest for a Markdown documentation bundle. Use when asked for a checksum manifest of a documentation folder.
allowed-tools: Bash(python3:*)
---

# Doc packager

Run the bundled script with `python3`, using the workspace root (the directory that contains `docs/`) as the working directory. The script is `scripts/build_manifest.py` relative to this skill's directory. It writes `out/bundle-manifest.txt`.
