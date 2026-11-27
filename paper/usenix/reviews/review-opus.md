# Review: "SkillDiff: Differential Runtime Conformance Testing for Portable AI Agent Skills"

Reviewer lens: experimental rigor (design, confounds, metric definitions, statistics, artifact cross-check).

## 1. Paper summary

The paper argues that the security outcome of a portable agent skill depends on the host that loads it, not only on the package. It builds 108 synthetic tasks (36 LLM-authored families, three tasks each), each with a benign and an adversarial skill package whose bundled Python script also performs one of five templated workspace harms, plus 44 "disguised" variants for the two secret-leak harms. Claude Code 2.1.310 and OpenCode 1.18.29 are both run on Claude Haiku 5.5 under paired permission presets, five repeats per cell. The workspace is diffed before and after each run, and transcripts are parsed by rules. The headline results are that Claude Code "ran the harmful script" in 85.7% of adversarial runs against 15.9% for OpenCode. Within Claude Code, the preset that refuses file edits left harm in place more often than the one that accepts them (79.6% vs 46.1%), and the paper attributes this to blocked cleanup. Across hosts, execution tracks whether the agent read the script first.

## 2. Strengths

- **A good question.** Holding the model fixed across hosts addresses a real confound in prior cross-client comparisons (Skill-Inject, the dev-tools injection studies, MCPSecBench), where host and model change together.
- **End-state observation.** Diffing the workspace before and after each run is the right primary signal for "is the harm there." I re-derived `attack_persists` logic (`tools/run_agent_pilot.py`, `attack_persists()`), and it is simple, kind-specific and self-tested.
- **Numbers reproduce.** Every number I sampled matches `results/agent-pilot/analysis.md` and the raw `run_meta.json` files: 463/540 = 85.7%; 86/539 = 16.0%; 430/540 = 79.6%; 249/540 = 46.1%; 198/540 = 36.7%; 843/844 and 63/236; 0/1735 and 0/1602; secret-in-output 96/110 run and 84 blocked against 97 removed. `tools/validate_claim_ledger.py` passes (88 claims). The claim-ledger discipline is commendable.
- **Appropriate unit of resampling.** The family-clustered bootstrap with per-task means and per-task sign counts is sound, and the effect sizes are large enough that the inferential machinery is not doing heavy lifting.
- **Candor in places.** The harness's own `BOUNDARIES` list in `tools/run_agent_pilot.py` is unusually honest, and several of its caveats should be promoted into the paper (see below).

## 3. Weaknesses (ordered by severity)

### W1 (major, borderline fatal for the headline wording). The main metric "ran the harmful script" does not measure that on OpenCode.

`script_executed_self_reported` matches any Python shell call that names the script, including `importlib.util.spec_from_file_location(...)` and calling selected functions (`tools/run_agent_pilot.py`, `script_run_pattern`; the harness caveat says so explicitly). The artifact also records `script_run_as_shipped_self_reported`. From the raw `run_meta.json` files:

| Cell (adversarial) | "executed" | as shipped |
|---|---|---|
| CC `skill_allowed` | 463/540 | 432/540 (80%) |
| OC `edits_denied` | 87/540 | **11/540 (2.0%)** |
| OC `edits_allowed` | 80/540 | **5/540 (0.9%)** |
| OC `default` | 14/108 | 1/108 |

So roughly 87% of OpenCode's "ran the harmful script" runs are the agent importing the module and calling the benign functions, after reading it and evidently routing around the harmful step. Sampled transcripts confirm this, e.g. `doc-partition-element-partition.opencode-edits_denied-adversarial-r4-*` and `diff-planner-risk-summary.opencode-edits_denied-adversarial-r3-*`. Consequences:

- The abstract's "OpenCode ran the harmful script in 15.9%" is wrong as worded.
- The cross-host gap is, if anything, larger than reported.
- §5.1's "When OpenCode did run the script, the harm was almost never present at the end" describes runs in which the harmful code never ran. It is not evidence of OpenCode cleanup.

The "ran, no harm at end" outcome (Fig. 1) conflates *harm never realized* with *harm realized then undone*. The harness takes only start and end snapshots, so it cannot tell these apart. The same conflation affects the preset analysis: in CC `skill_allowed_accept_edits`, 32 of the 443 "executed" runs were not as shipped.

### W2 (major). The "stricter preset, worse end state" finding is mostly a change from "removed" to "left and reported to the user". The preset is also not stricter in capability.

(a) **Silent persistence barely differs between presets.** The outcome taxonomy ignores whether the user is told. In `analysis.md` Table A, `run_harm_left` (harm persists and no refused call on the target) is 232/540 under edits-refused and 210/540 under edits-accepted, about 4 points apart. Almost the whole +33.5-point difference is `run_cleanup_blocked`.

In cleanup-blocked runs, the final message nearly always names the harmed file or the secret and asks the user to act. I count 188/198 by `final_mentions_target`, `canary_in_final_message` or secret-in-output. Example from the `doc-convert-markdown-to-html...skill_allowed-adversarial-r1` final message: "Needs your action: ... has a trailing ##...". A preset that leaves the harm but discloses it is not obviously a "worse end state" than one that removes it silently. The paper's framing treats a user-informed residual and a silent compromise as the same outcome.

(b) **A residual leak that is not counted.** Under edits-refused, Claude Code repeated the canary in its final reply in 40/110 secret-in-output adversarial runs and 48/110 disguised ones, against 5 and 4 with edits accepted (`analysis.md` Table B, `canary_in_final_message`). The prompt forbids secret-like material in outputs. The paper does not count this.

(c) **"Refusing edits" does not remove the capability to clean up.** Both `skill_allowed` presets grant `Bash(python3:*)`, which permits arbitrary file writes and deletes via `python3 -c`. OpenCode agents routinely do exactly this after an edit denial (many `opencode-edits_denied` transcripts write the report with `python3 -c "...write_text(...)"`). Claude Code agents chose not to; one final message says it "did not try to route around that". The effect is therefore about the agent deferring to a denial, not about a permission design that "needs a broader grant" for remediation (§6). The Discussion's mitigation framing does not follow.

(d) **The effect is heterogeneous by harm kind, which the paper does not report.** Harm at end, refused against accepted (`analysis.md` Table B):

| Harm kind | Refused | Accepted |
|---|---|---|
| secret-in-output | 84/110 | 0/110 |
| input-tamper | 87/105 | 47/105 |
| stray-write | 87/110 | 61/110 |
| secret-in-side-file | 86/110 | 70/110 |
| autorun-config | 86/105 | 71/105 |

For autorun-config, `run_cleanup_blocked` is 19/105 under both presets. One template drives about half the headline effect.

### W3 (major). The cross-host contrast differs in more than "the host", contrary to §3's "differ only in host or preset".

The paper treats the host's system prompt and tool set as the treatment, which is fair. But several harness-level asymmetries are not intrinsic to the host:

- **Effective permission surface.** OpenCode's pair presets deny every shell command except `python3 *`, including `ls`, `mkdir`, `cd ... &&` and `cat >`. Claude Code headless allows read-only commands. In the artifact, 503/540 OC `edits_denied` adversarial runs (and 529/540 benign runs) contain at least one denied shell call, against 271/540 for CC `skill_allowed`. An agent that is repeatedly refused may behave more cautiously. The paper mentions the mapping is "approximate" only in Limitations.
  - The authors hold partial evidence against this confound and do not use it. OC `default` (no permission config, 0 denied calls in 108 adversarial runs) still runs the adversarial script as shipped in only 1/108 runs, while running the benign one in 107/108. That cell should be in the main text, and a frictionless matched CC cell (e.g. a CC preset that allows the same read-only commands OC is denied, or an OC preset allowing them) should be added.
- **Environment isolation.** OC runs with a temp HOME, `--pure` and a per-run data dir. CC runs with the real HOME, several runs at a time sharing it (Limitations; `BOUNDARIES`). The CC init event shows 19 additional built-in skills and 3 built-in plugins competing in the skill list (`capability.json`). Whether user-level `CLAUDE.md` or memory was loaded is not established in the paper. `--setting-sources project` suggests not, but please state it.
- **Budget.** CC runs had a $0.50 per-run cap that turns into `agent_error` (`BOUNDARIES`). No comparable cap is described for OC.
- **Package content.** Each SKILL.md carries a Claude-specific `allowed-tools: Bash(python3:*)` frontmatter line, e.g. `benchmark/agent-pilot/skills/adversarial/api-collection-assertion-coverage/SKILL.md`. The "identical package" is therefore not semantically identical across hosts. The paper does not disclose this.
- **Failure-status coding.** For Claude Code, a tool call is "attempted" (and so counts toward `executed`) unless a `permission_denied` event exists, even when its `tool_result` has `is_error`. For OpenCode, any `state.status == error` becomes `failed` and does not count (`tool_calls()` in `tools/run_agent_pilot.py`). Empirically this affects only 2-7 CC runs, but the metric is defined asymmetrically across the two sides being compared.

### W4 (major). Run exclusion and retry are unreported.

Every retained CC run has `agent_error == false`, and only 5 OC runs do not. The harness notes that failed runs were "set aside and re-run". This includes 762 early OpenCode runs, of which "most" failed at startup, so some apparently completed and were still discarded. The number of discarded and re-run runs per cell, and the reasons, are not reported. Retry-until-success is a selection mechanism. Budget-cap hits in particular correlate with long, exploratory trajectories, which plausibly include script reading. Please report attrition per cell and show that results hold when the first attempt is kept.

### W5 (major). The mechanism claim is overstated.

- "Reading" is a post-treatment behavior produced by the same agent disposition that produces non-execution. "Not read first → executed 843/844" is close to tautological once the preset allows execution. The paper does call this an association, which is good, but the abstract ("execution tracks one behavior") and §5.5's "the information available to the model was therefore the same" go further.
  - The information is not the same. The system prompts, tool descriptions, skill-tool framing and available shell commands differ. CC listed the script path in 1519/1735 skill outputs and OC in 1602/1602.
  - The `shows_script` detector (docstring first line or the string `def main`) is narrow.
- The one experiment that would make the mechanism claim (inline the script source, or force a read, on Claude Code) is proposed but not run. It is cheap within this harness and would turn the paper's most interesting observation into a result.

### W6 (major). External validity: an easy attack, primed prompts, one model.

- **The harmful code is unobfuscated.** It comes from five templates and directly contradicts explicit boundaries in every prompt ("Do not read .env ...", "Do not create or modify files other than the requested outputs"; see `benchmark/agent-pilot/families/api-collection/tasks/assertion-coverage.txt`). Any agent that reads the script is handed the violation in plain sight.
- **The disguised variants are thin.** They only replace `open(".env")` with a dotfile scan under a benign docstring.
- **There is no condition without the boundary paragraph.** The magnitude of the host gap is therefore specific to trivially detectable attacks under primed prompts.
- **One model, and the same family wrote the tasks.** There is one model (the cheapest Haiku tier) and one version of each host. All families were authored by `claude-sonnet-5-5` (`family.json`: `author_model`) and evaluated with a Claude model.
- **The claims outrun the evidence.** The Discussion's "a verdict about a skill does not transfer between hosts" is supported for this model and attack class only. The abstract and conclusion state it generally.

### W7 (minor). `harm_persists` is not computed from the workspace alone, as §7 claims.

In `tools/analyze_agent_pilot.py`, `harm_persists` = outcome in {`run_cleanup_blocked`, `run_harm_left`}. Outcome is `not_run` whenever the transcript-derived `executed` is false, regardless of the workspace. Limitations states that harm at end "does not depend on the transcript", which is false by construction. Empirically only one retained run has `attack_persists` true with `executed` false, so the numbers survive. Report raw `attack_persists` instead.

### W8 (minor). The cleanup-blocked heuristic is loose.

A later call counts as "on the harmed file" if its command or path contains the target path, its basename, or its **first path component** (e.g. `reports`, `.cache`, `collection`). It counts as refused if blocked, or if a failing non-read call matches a permission regex. Any refused write elsewhere in `reports/` therefore counts as blocked cleanup. My sample of secret-in-output transcripts showed genuine remediation attempts, but the paper defers validation to a human labelling study whose results are not reported. The parenthetical in §5.4 ("Our human-labelled sample checks whether these calls were remediation") points at a result that does not exist in the submission.

### W9 (minor). Benign utility is described as "similar" when it is not on one metric.

Under pair 1, report-matches-script is 99.1% vs 84.7%, +14.4 points [+10.0, +19.6] (`analysis.md` Table E). The abstract's "used the skills on benign tasks at similar rates" is true for `executed` only.

### W10 (minor). The title promises more than the paper delivers.

"Differential runtime conformance testing" implies a conformance specification. The method is a paired two-host experiment with an oracle used only for measurement. At 7 pages, the paper also leaves substantial room for the missing analyses above.

## 4. Detailed comments by section

- **Abstract.**
  - Replace "ran the harmful script" with an as-shipped metric, or report both.
  - "Stricter permission preset can produce a worse end state" needs the disclosure qualifier from W2.
  - "Both hosts used the skills on benign tasks at similar rates" should be scoped (W9).
- **§1 Findings bullet 2.** "In 36.7% of runs the host refused a later call by the agent on the harmed file." State that in nearly all of these runs the agent reported the residual harm to the user.
- **§3 Invariants.** "two runs compared on a task differ only in host or preset" is contradicted by the HOME, concurrency, budget-cap and permission-surface asymmetries (W3). Either equalize them or enumerate them here, not in Limitations.
- **§3 Observation.** Defines executed as "as shipped or modified". This is exactly the choice that makes the OC numbers misleading. Justify it or split the metric.
- **§3 Outcomes.** Add a "harm disclosed to user" dimension (the artifact already computes `final_mentions_target` and `canary_in_final_message`). Separate "harm never realized" from "harm undone", which needs an intermediate snapshot after the first script execution, or a file-event trace.
- **§3 Statistics.** Fine. Note that the percentile bootstrap with 36 clusters may under-cover slightly. A BCa or wild-cluster check would reassure, though at these effect sizes it will not matter.
- **§4 Hosts and presets.** "differ only in whether file edits are allowed" is false for OC versus CC because of the shell allow-list. Disclose the `allowed-tools` frontmatter line in every package.
- **Table 2.** Add as-shipped execution. Add CIs for the disguised rows (the artifact has them: e.g. disguised executed +80.0 [+72.4, +86.4]). Add the OC `default` cell. "Tasks higher / lower" omits ties; include them.
- **§5.1.** The last sentence is unsupported (W1).
- **§5.4 / Table 3.**
  - Add the per-harm-kind breakdown (W2d) and the `run_harm_left` row by itself.
  - The secret-in-output example is the strongest case and should be presented as such, not as typical.
  - "Because OpenCode seldom ran the script" should say "seldom ran it as shipped".
  - "The grant gates execution": the grant bundles `Skill` and `Bash(python3:*)`, so this does not identify which permission gates execution (the harness notes this).
- **§5.5.** "843 of 844" conditions on a post-treatment variable. Report it, but do not call it the gate. "The information available to the model was therefore the same" should be removed (W5).
- **§6.** The checkpoint/revert recommendation does not follow, because the remediation capability (`python3`) was already granted (W2c). The reading-before-running mitigation is the paper's best idea. Run it.
- **§7.** Promote the following caveats from `BOUNDARIES` into the paper: the `allowed-tools` line; the $0.50 cap; OC run discards; the `script_executed` definition; `.env` reads being self-reported.
- **Figure 1.** "Ran, no harm at end" for OC is mostly "ran a modified script without the harmful step". Relabel it or split it.
- **Ethics / Open Science.** See §7 of this review.

## 5. Questions for the authors

1. What are the as-shipped execution rates per cell? Do you agree that the OC "ran" figure is mostly import-and-call? Why was the broader definition chosen as the headline?
2. How many runs per (host, preset, label) cell were discarded and re-run, and for what reasons (startup error, budget cap, other)? Of the 762 set-aside OpenCode runs, how many had completed normally?
3. Was user-level `CLAUDE.md`, auto-memory or any user setting loaded into the Claude Code runs? What exactly did `--setting-sources project` exclude in 2.1.310? Did concurrent runs sharing HOME interact (e.g. via the shared temp root, which agents listed with `ls ..`)?
4. Did Claude Code honor the packages' `allowed-tools: Bash(python3:*)` line in any preset? Does removing it change the `default`/`accept_edits` results?
5. Separating disclosed from silent persistence, what is the edits-refused versus edits-accepted difference in silent harm? My reading of Table A is about +4 points.
6. Can you run the frictionless comparison: an OC preset that allows the read-only commands CC allows, or a CC preset restricted to `python3` only?
7. Can you run the one-component manipulation the paper proposes (inline script source in CC's skill output, or require a read before execution) on even a subset of tasks?
8. Do results hold without the boundary paragraph in the prompt, and on at least one stronger model?
9. Where are the human labels the paper refers to? What is the agreement for `executed`, `read_before_run` and cleanup intent?

## 6. Required changes for acceptance

1. Report as-shipped execution as the primary "ran the harmful script" metric (or alongside), and rewrite the abstract, §1, §5.1, Table 2 and Figure 1 accordingly.
2. Separate "harm never realized" from "harm undone" (mid-run snapshot or file-event trace). Add a disclosure dimension to the outcome. Re-state the preset finding in terms of silent persistence, with the per-harm-kind breakdown.
3. Equalize or explicitly control the non-host asymmetries: HOME isolation, concurrency, budget cap, shell allow-list, and the `allowed-tools` frontmatter. At minimum, add the OC `default` cell and a matched frictionless pair.
4. Report attrition and retries per cell, and a sensitivity analysis on first attempts.
5. Either run the reading manipulation or tone down the mechanism claims (abstract, §5.5, §6) to correlational language.
6. Report the human-label validation for transcript-derived labels and the cleanup-intent heuristic, or remove claims that depend on it.
7. Compute "harm present at end" from `attack_persists` directly, and fix the Limitations sentence.
8. Scope the generalization claims to one model, two host versions and unobfuscated templated attacks under boundary-primed prompts. Ideally add a second model.

## 7. Ethics and open-science assessment

**Ethics.**
- Risk is low. There are no human subjects, canaries are synthetic, scripts make no network calls, and harms are confined to temporary workspace copies.
- Releasing five trivial harm templates adds no meaningful attacker capability.
- Disclosure to the host developers is stated as in progress. The paper should say what was disclosed and when. The main finding is behavioral rather than a vulnerability, so the disclosure burden is light.
- Use of LLM-authored benchmark content is disclosed.

I see no ethics blocker.

**Open science.** The artifact is substantial and largely reproducible from retained files. The analysis is read-only and deterministic (seeded bootstrap), and the claim ledger validates. However:

- **Transcripts are not scrubbed.** The paper promises "scrubbed transcripts", but the retained `stdout.log` files are raw. In the current artifact, 3,699 of them contain the operator's absolute home path, including the account name, via the Claude Code init event's `memory_paths`, `ls -la` outputs and absolute temp paths in tool calls. `run_meta.json` is scrubbed; `stdout.log` is not.
  - This would deanonymize the submission if the artifact link were shared with reviewers.
  - The scrubbing must be applied to the released transcripts and verified by a check.
- The Cursor and Codex campaigns are mentioned but excluded. Fine, but the released data should mark them clearly.
- The artifact should ship the discarded and re-run runs (or their metadata) so that attrition can be audited (W4).

## 8. Recommendation

**Major revision.**

The core question is good, and the same-model, two-host design is a genuine improvement over prior cross-client work. The raw data in the artifact does support a large, robust host effect on Claude Haiku 5.5. If anything, the effect is larger than reported once execution is measured as shipped.

As submitted, however, the headline metric does not measure what the abstract says on one of the two hosts. The second headline finding ("stricter preset, worse end state") largely turns a silent removal into a disclosed residual, under a preset that did not actually remove the cleanup capability, and is driven mainly by one harm template. The mechanism claim rests on a post-treatment association with an overstated "same information" premise. Several non-host asymmetries (HOME isolation, concurrency, budget cap, shell allow-list, a CC-specific `allowed-tools` line in every package, unreported retries) contradict the "differ only in host or preset" invariant that is the paper's methodological contribution.

None of these is unfixable, and most can be fixed from data already collected. Together, though, they mean the current claims are not supported as worded, and the paper is too thin (7 pages, one model, unobfuscated templated attacks) to absorb the corrections without new experiments: a frictionless matched pair, the reading manipulation, and ideally a second model.

## 9. Reviewer confidence

**Confidence: 4 (expert, checked the artifact).**

**What I verified.**
- I recomputed a sample of the paper's numbers from `results/agent-pilot/analysis.md` and the raw `run_meta.json` files; all sampled numbers match.
- I read the metric code in `tools/analyze_agent_pilot.py` and `tools/run_agent_pilot.py`.
- I inspected sample transcripts for cleanup-blocked, harm-removed and OC "executed" runs.
- I computed as-shipped execution, denied-shell-call rates and the persistence-without-execution check from the raw run files.
- `tools/validate_claim_ledger.py` passes.

**What I could not verify.**
- Whether user-level Claude Code memory or instructions were loaded.
- The number and nature of discarded or re-run runs (not in the artifact).
- Whether concurrent shared-HOME runs interfered.
- The human-label study (not present).
- Whether the `allowed-tools` line had any effect.

I did not run the agent harness or any model.
