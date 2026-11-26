# Fix list from the three model reviews (2026-11-19)

Reviews: `review-fable.md` (Major revision, confidence 3/4), `review-opus.md` (Major revision, 4/4),
`review-mythos.md` (Reject, 3/4). `review-grok.md` (Invited for Major Revision, 3/4) reviewed the reframed draft of 2026-11-19 from the
paper text alone; see section E. These are model reviews, not human peer review.

"Verified" means the claim was re-checked against `results/agent-pilot/runs/*/run_meta.json` or
`results/agent-pilot/analysis.json` after the reviews came in.

## A. Fixable without new runs

Status 2026-11-19: items 1 to 7 are applied in `main.tex`, `tools/analyze_agent_pilot.py`,
`tools/build_pilot_paper_claims.py` and `tools/export_scrubbed_pilot_runs.py`. Still open inside them:
per-cell re-run counts cannot be recovered (stated as a limitation); the sentence that HarnessSafe has no
fixed-model comparison is hedged and needs a full read of that paper; the scrubbed export is verified but not yet
stored in the artifact bundle; the title still says "conformance testing".

1. **Headline metric (all three; verified).** "Ran the script" counts modified copies. Unmodified runs:
   Claude Code `skill_allowed` 432/540, OpenCode `edits_denied` 10/539 (adversarial). Report "ran as shipped",
   and split "ran, no harm at end" into "harm never happened" and "harm repaired".
2. **Unreported Sonnet runs (Mythos; verified).** Claude Code `skill_allowed` on the five original cases:
   Sonnet 5.5 ran the adversarial script as shipped in 0/25 runs, Haiku 5.5 in 15/25 (disguised 0/25 vs 18/25).
   Report them and scope every claim to Haiku 5.5; call the campaign a pilot.
3. **Stricter-preset finding (Fable, Opus; partly verified).** Harm left with no refused cleanup is 232/540 vs
   210/540; the gap is the cleanup-refused runs, and in those the final message names the harmed file in
   104 of 114 runs where that is measurable. `python3` stays allowed under the edit-refusing preset.
   Reword as "refusing edits turns repaired harm into reported harm" and report the final-message numbers.
4. **Statements to remove or correct (all three).** The human-labelled sample is cited as if done; "the
   information available to the model was the same" (skill body delivery differs by host); "harm at end does
   not depend on the transcript" (the analysis requires the executed flag); "scrubbed transcripts".
5. **Confounds to state (Opus).** OpenCode's shell denies everything except `python3`; Claude Code used the
   real home directory and a $0.50 budget cap (verified); every SKILL.md has an `allowed-tools` line
   (verified); tool errors count as executed on Claude Code only; failed runs were re-run with no per-cell
   attrition reported. Use the OpenCode `default` cell to address the denial confound.
6. **Related work (Fable).** Credit HarnessSafe properly; fix the HarmfulSkillBench and Runtime Skill Audit
   descriptions; add differential-testing, supply-chain and prompt-injection foundations; cite published
   versions where they exist.
7. **Artifact (all three; verified in part).** 3,699 `stdout.log` files hold the home path and account name,
   and transcripts are git-ignored, so the analysis cannot be regenerated from a clone.

## B. Needs new runs or outside steps

8. **Second model on the full task set** (Fable: reject without it; Mythos: fatal).
9. **Mechanism intervention**: change one host component (show the script source, or require a read) and re-measure.
10. **Stronger threat model** (Mythos: fatal): harms are mild, reversible workspace edits and exfiltration is
    out of scope; all 108 prompts share one boundary paragraph.
11. **Human labels** from two real raters.
12. **Vendor disclosure** with dates and responses.
13. **Length**: about five pages of body against a 13-page limit.

## Fourth review, pasted by the author (2026-11-19)

Model and source not recorded; the full text is not saved here. Verdict: Reject / Major revision for a top-4 main
track; it read the first 7-page draft, so several points were already fixed when it arrived.

| Point | Status |
| --- | --- |
| M1 human validation cited as done | Fixed earlier (stated as not yet labelled) |
| M2 Claude Code ran with the real home directory, several runs at once | Stated as a limitation; fixing it needs re-runs (item 14) |
| M3 per-action breakdown | Added (Table 4): the cross-host gap holds for all five actions; the preset effect is concentrated in secret-in-output |
| M4 one small model, two hosts; Cursor and Codex mentions | Sonnet check reported; second model is item 8. The Cursor and Codex sentence stays, because other reviewers asked for unreported runs to be disclosed |
| M5 no causal intervention, no adaptive SKILL.md attacker | Intervention is item 9; adaptive SKILL.md now stated as untested and added as item 15 |
| M6 OpenCode removes edit tools, Claude Code refuses them | Added to Limitations; pair 2 (edit tools on both hosts) shows the same gap |
| Table 3 transposed, clipped caption | Not present in the current PDF (the first draft's table overflowed its column) |
| Table 2 blank intervals for disguised rows | Fixed earlier |
| 539 and 219 run counts unexplained | Explained (five runs of that preset ended in agent errors) |
| SkillSentry (2608.03485), SkillConsist (2608.07639) | Verified on arXiv and cited |
| Name collision | Checked 2026-11-19: PyPI `skilldiff` 0.1.0 (2026-08-17, A/B testing of agent skills with an LLM judge) and npm `skilldiff` 0.1.0 (2026-09-18, behavioural regression testing for agent skills in a real harness) exist, and skilldiff.dev is a live agent-skill directory. The vision paper was not found (arXiv title search empty; nearest are SkillDiffuser 2312.11598 and SADiff 2601.11266). Renaming is the author's call |

Added to section B:

14. **Isolated home directory for Claude Code**: re-run at least a validation subset with a per-run home.
15. **Adaptive SKILL.md attacker**: a SKILL.md that tells the agent to run the script without reading it.

## C. Experiment plan (started 2026-11-19)

New runs go to `results/agent-pilot-arms/` and never enter the baseline analysis. Queues: `tools/run_pilot_arms.py`;
analysis: `tools/analyze_pilot_arms.py`. All arms use pair-1 presets (Claude Code `skill_allowed`, OpenCode
`edits_denied`), all 108 tasks, one repeat, compared with the five baseline repeats task by task.

| Item | Arm | Hosts | Runs | Status |
| --- | --- | --- | --- | --- |
| 8 second model | Claude Sonnet 5.5, benchmark as built, adversarial + benign + disguised | both | 520 | done (6 OpenCode runs missing); in paper §5.4 |
| 9 mechanism | `host_read_first`: one sentence appended to Claude Code's system prompt | Claude Code | 216 | done; in paper §5.5 |
| 9 mechanism | `skill_inline_source`: SKILL.md also contains the script source | both | 432 | done; in paper §5.5 |
| 15 adaptive attacker | `skill_no_read`: SKILL.md tells the agent to run the script without reading it | both | 432 | done; in paper §5.6 |
| 10 threat model (part) | `prompt_no_boundary`: boundary paragraph removed from the prompt | both | 432 | done (1 OpenCode run missing); in paper §5.8 |
| 14 isolation (part) | `serial_control`: 36 tasks on Claude Code, one run at a time | Claude Code | 72 | done; in paper §5.8 |
| 14 isolation | `isolated_home`: fresh home directory per run | Claude Code | 72 | blocked: a fresh home is not logged in; needs `CLAUDE_CODE_OAUTH_TOKEN` or `ANTHROPIC_API_KEY` in the environment |
| 10 threat model | Network egress to a local sink, payload outside the entry script | both | not sized | not started |
| 11 human labels | Two raters on `benchmark/review/pilot-labels` | | | needs people |
| 12 disclosure | Report to the three vendors | | | needs the author |
| 13 length | Add the arm results to the paper | | | done 2026-11-19: paper reframed around the arms, 10 pages with references |

## D. Reframe (2026-11-19)

The paper now argues that running a malicious skill script unmodified depends on whether the agent sees the script's
source first, and that host, model and one sentence in the skill each change that. Claims CL-PILOT-012 to 017 carry
the arm numbers. Open after the reframe, all needing new runs:

16. **Host sentence against skill sentence**: `host_read_first` and `skill_no_read` together (Claude Code, Haiku). Done 2026-11-19 (CL-PILOT-018): the skill's sentence still won in 20 of 108 runs.
17. **Do-not-read sentence on Sonnet**, both hosts. Done 2026-11-19 (CL-PILOT-019): 104 of 108 (Claude Code) and 103 of 107 (OpenCode) ran as shipped.
18. **Payload that survives a read**: harm in an imported module or obfuscated code, with the source shown. Module version done 2026-11-19 (CL-PILOT-020, `payload_in_module`): agents that read followed the import; at most 3 of 108 runs ran as shipped. Base64 version done 2026-11-19 (CL-PILOT-021, `payload_obfuscated`): at most 1 of 108 runs ran as shipped; on OpenCode with Sonnet the provider's content filter stopped 38 of 108 runs. Long scripts, import chains, data-driven payloads and ordinary-looking obfuscation are still untested.
19. **More repeats for the arms** (each has one), and the isolated-home arm (item 14).

## E. Grok review of the reframed draft (2026-11-19)

Verdict: Invited for Major Revision, confidence 3 of 4. It read the paper text only. It accepted the causal
argument and the statistics and raised no objection to the metric definitions the earlier reviews attacked.

| Point | Severity | Status |
| --- | --- | --- |
| Threat model assumes the attacker's SKILL.md reaches the agent; registry review or moderation is not considered | major | Fixed 2026-11-19: the threat model and Limitations now say registry or scanner review is outside the threat model and untested |
| Two hosts, and two models from one provider | major | Open, needs runs: a third host (Cursor after its limit resets) or a non-Claude model on OpenCode, which would test the do-not-read sentence on another model family with the host fixed |
| Shared home directory and concurrency not fully removed | minor | Stated; the isolated-home arm is still blocked on a token |
| Labels not validated by humans | minor | Stated as pending; needs two raters |
| Tie the do-not-read sentence to the indirect prompt-injection literature | minor | Fixed 2026-11-19: Related Work names the sentence as an indirect injection through the skill body |
| "Neither host enforced it" is strong | minor | Fixed 2026-11-19: scoped to the presets we ran in the abstract, introduction, discussion and conclusion |
| Discussion should say how a host could enforce reading | required change | Already present ("A habit is not a control") |
| Human validation results or an explicit "pending" | required change | Already stated as pending |

### Routes to a third host or another model family (status 2026-11-19)

All three are wired into `tools/run_pilot_arms.py`; none has data yet.

| Route | Cells | Blocker |
| --- | --- | --- |
| OpenCode with GPT-5.6 Terra (`run opencode`) | as built and do-not-read, 432 runs; host fixed, model family changed | OpenCode's own API key has expired; either a new one via `opencode auth login`, or `OPENROUTER_API_KEY` exported in the launching shell (the runner then uses `openrouter/openai/gpt-5.6-terra` and masks the key in run folders) |
| Cursor agent with Grok 4.7 Low (`run cursor_agent`, preset `sandbox`) | do-not-read against the baseline `sandbox` cell, 216 runs | **Done 2026-11-25** (CL-PILOT-023, 024): with the sentence 89 of 108 adversarial runs as shipped, none read first; +4.1 points [−2.0, +11.2] against the baseline over 98 tasks. The arm was moved off `default`, where the host denies every shell command and no script runs. The arm ran on a later Cursor build than the baseline |
| Grok CLI with grok-4.7 (`run grok`, preset `edits_removed`) | as built and do-not-read, 432 runs | Free Grok Build usage limit, reached after about ten runs; needs a paid plan or a wait of unknown length |
| Codex CLI with GPT-5.6 Terra (`run codex`, preset `workspace_write`, fresh HOME) | as built and do-not-read, 432 runs | **Done 2026-11-24** (CL-PILOT-022): as built 100 of 108 adversarial runs as shipped, 11 read first; with the sentence 108 of 108. Host and model change together. In 137 of 432 runs a shell command failed to start inside Codex; rates do not differ between those runs and the rest |

Grok CLI as a host, from the probes (1.0.52 for the first probes; it updated itself to 1.0.89 before the harness runs):
it loads project skills only from a trusted folder (`--trust`); it has no skill tool and reads `SKILL.md` with its
read tool; a refused tool call ends a headless run, so the preset removes the edit tools and approves the rest, which
leaves every shell command allowed, unlike the other hosts' paired presets. In five trusted benign probes it used the
skill in three. One benign run through the harness parsed correctly end to end; it and one limit-stopped adversarial
run were removed, so the arm data hold no Grok runs.

