---
name: content-extract
description: Tags prose files with a likely language from common-word counts and flags low-confidence results. Use when asked for a language tag report on a folder of text documents.
allowed-tools: Bash(python3:*)
---

# Content extract

Run the bundled script with `python3`, using the workspace root (the directory that contains `samples/`) as the working directory. The script is `scripts/tag_languages.py` relative to this skill's directory. It writes `reports/language-tags.md`.
