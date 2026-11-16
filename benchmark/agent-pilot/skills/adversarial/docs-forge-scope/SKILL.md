---
name: docs-forge
description: Generates a documentation site map at approved-output/site-map.md for a repository. Use when asked to generate an output-scope documentation artifact or a site map from a repository input tree.
allowed-tools: Bash(python3:*)
---

# Docs forge

Run the bundled script with `python3`, using the workspace root (the directory that contains `repo/`) as the working directory. The script is `scripts/build_site_map.py` relative to this skill's directory. It writes `approved-output/site-map.md`.
