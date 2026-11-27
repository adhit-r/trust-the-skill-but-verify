# USENIX Security 2027 draft

The paper calls the method HostDiff (renamed from SkillDiff on 2026-11-19 because that name is taken by
published agent-skill packages). The repository's Python package and older planning notes still say SkillDiff.

The paper's argument (reframed 2026-11-19 around the second-model and intervention arms): whether an agent runs a
malicious skill script unmodified depends on whether it sees the script's source first, which the host, the model
and one sentence in the skill each change.

`main.tex` is the manuscript. Every HostDiff number in it is a `CL-PILOT-*` claim in
`paper/claim-ledger.json`, checked by `python3 tools/validate_claim_ledger.py`.

Regenerate inputs, then build:

```bash
python3 tools/analyze_agent_pilot.py > /dev/null     # results/agent-pilot/analysis.{json,md}
python3 tools/analyze_pilot_arms.py                  # results/agent-pilot-arms/analysis.{json,md}
python3 tools/build_pilot_paper_claims.py            # CL-PILOT-* claims and numbers.tex (baseline and arms)
python3 tools/build_pilot_outcome_figure.py          # fig-pilot-outcomes.tex
python3 tools/validate_claim_ledger.py
cd paper/usenix && latexmk -pdf -outdir=build main.tex
```

`main.tex` takes every number from `numbers.tex`; do not type results into the text.

For release, `python3 tools/export_scrubbed_pilot_runs.py --out <dir> --verify` writes the run metadata and
transcripts with local paths and the account name removed, and checks that the analysis reproduces on them.

`reviews/` holds model-written reviews of the draft and the fix list drawn from them.

`usenix2019_v3.sty` is the official style from usenix.org (Author Resources, Paper Templates).
It needs the TeX Live packages `sttools` (for `flushend`), `breakurl`, `rsfs` and `zapfchan`,
which basic TeX Live lacks (`tlmgr --usermode install sttools breakurl rsfs zapfchan`); without
the first three, `main.tex` falls back to an approximation of the style's page geometry, good for
page counts only, and says so in the log. `refs.bib` holds
arXiv metadata fetched on 2026-11-19.
