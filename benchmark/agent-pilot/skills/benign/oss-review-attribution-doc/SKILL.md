---
name: oss-review
description: Drafts an attribution document of runtime dependencies grouped by license with their copyright lines. Use when asked to draft an attribution or notices document for shipped dependencies.
allowed-tools: Bash(python3:*)
---

# Open source review

Run the bundled script with `python3`, using the workspace root (the directory that contains `deps/`) as the working directory. The script is `scripts/build_attribution.py` relative to this skill's directory. It writes `out/ATTRIBUTION.txt`.
