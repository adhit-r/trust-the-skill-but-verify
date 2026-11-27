# Review: SkillDiff: Differential Runtime Conformance Testing for Portable AI Agent Skills

Venue: USENIX Security 2027 (Cycle 2). Reviewer lens: significance, threat model, presentation.
Reviewed: `paper/usenix/main.tex`, `paper/usenix/build/main.pdf`, `paper/usenix/refs.bib`, `paper/usenix/fig-pilot-outcomes.tex`, and the artifact (`results/agent-pilot/`, `paper/claim-ledger.json`, `tools/run_agent_pilot.py`, `tools/analyze_agent_pilot.py`, `benchmark/agent-pilot/`). I did not run the agent harness. I re-read stored run metadata and transcripts with read-only scripts.

## 1. Paper summary

The paper argues that the security outcome of an agent skill depends on the host that loads it, and tests this by running identical skill packages, prompts and workspaces on Claude Code 2.1.310 and OpenCode 1.18.29 with the same model ID (Claude Haiku 5.5). The benchmark is 108 tasks in 36 LLM-authored families, each with a benign package and an adversarial one whose script adds one of five templated workspace changes, plus 44 "disguised" packages. Claude Code is reported to run the adversarial script in 85.7% of runs against 15.9% for OpenCode, with the change still present at the end in 79.6% against 0.9%. Within Claude Code, a preset that refuses file edits leaves the change in place more often than one that accepts them (79.6% against 46.1%), because the agent's later calls on the changed file are refused. The paper attributes the cross-host gap to whether the agent reads the script before running it.

## 2. Strengths

- The question is well chosen. Holding the model ID fixed while changing the host removes the confound that most cross-host comparisons have, and the paper says so clearly.
- The end state is observed from the workspace diff rather than from the agent's account, and that part of the measurement does not depend on transcript parsing.
- The cross-host effect is very large and consistent on this benchmark (higher on 105 of 108 tasks). The benign-utility control rules out the trivial explanation that OpenCode simply does not use skills.
- The preset result (refusing edits blocks the agent's own repair) is a non-obvious observation, and the secret-in-output slice is clean: 84 of 96 runs blocked against 97 of 97 repaired.
- Statistics are appropriate for the design: per-task pairing and a family-cluster bootstrap.
- The paper is frank about several limits (association not manipulation, templates, one model), and the harness lists its own caveats in `tools/run_agent_pilot.py`.
- Numbers in the paper match `results/agent-pilot/analysis.md` everywhere I checked.

## 3. Weaknesses, ordered by severity

**W1 (fatal). The threat model and the harm definitions do not support security conclusions.**
The attacker controls a script that the host executes. Such an attacker wins at execution time, by exfiltration or arbitrary code execution, and the paper puts exactly those out of scope (§2). What is measured instead are five low-severity, reversible, local changes. Reading the packages confirms this: `stray-write` writes a filename index beside the inputs, `input-tamper` appends a `Reviewed-by:` line, `secret-in-side-file` copies `.env` into `.cache/` in the same workspace, and `autorun-config` writes a task that runs `echo`. These are "harm" only relative to one boilerplate paragraph that is byte-identical in all 108 prompts ("Do not read .env ... Do not create or modify files other than the requested outputs"). The headline metric "harm present at end" therefore does not correspond to attacker success, and the preset finding (cleanup blocked) only exists for harms that an edit can undo. For any realistic payload the only relevant number is whether attacker code ran.

**W2 (fatal). The evidence is a single design point and the conclusions are general.**
Two hosts, one version each, one model (the smallest tier), runs collected over three days. The abstract concludes that "a verdict about a skill does not transfer between hosts" and the conclusion that skill security "is a property of the skill and the host together". With one host pair the paper has an existence proof at most. The artifact also contains evidence that the effect is model-dependent, which the paper does not report: `results/agent-pilot/runs` holds Claude Code runs on `claude-sonnet-5-5` for the five original cases. Under `skill_allowed`, Haiku ran the adversarial script as shipped in 15 of 25 runs and Sonnet in 0 of 25; for disguised packages 18 of 25 against 0 of 25. The sample is small and uses the older prompts, but it points the opposite way from the paper's framing: on the same host, changing the model removed the behavior. §7 lists the Cursor and Codex campaigns and omits this one.

**W3 (fatal as submitted, administrative). The open-science requirement is not met.**
The Open Science section says the artifact "will" be released "at an anonymized link for review" and gives no link. Reviewers cannot inspect anything from the submission itself. Details in §7 below.

**W4 (major). The headline metric "ran the harmful script" is wrong for OpenCode.**
`executed` counts any successful `python3` call that names the script, including imports. From `run_meta.json`, OpenCode ran the script *as shipped* in 10 of 539 pair-1 runs (1.9%) and 5 of 540 pair-2 runs (0.9%). The other 76 of the 86 pair-1 runs counted as executed were not as-shipped runs, and all 76 ended with no harm. At least 70 of them are inline imports of the module with the harmful function stubbed or only helpers reused (for example `m.write_source_index = lambda: None; m.main()`), so the harmful code never ran. The abstract's "OpenCode [ran the harmful script] in 15.9%" is therefore false as worded, and §5.1's "when OpenCode did run the script, the harm was almost never present at the end" misdescribes sanitized execution as execution followed by a clean end state. The same applies to Claude Code: of the 33 "no harm at end" runs under `skill_allowed`, 30 are modified-only runs; only 3 of 432 as-shipped runs ended clean, against 162 of 411 with edits accepted. The corrected numbers make both findings stronger, but the paper's categories ("ran", "ran, no harm at end") do not mean what a reader takes them to mean. The harness's own caveat list states this conflation; the paper mentions it in half a sentence in §3.

**W5 (major). The mechanism claim is not established, and one supporting statement is contradicted by the transcripts.**
§5.5 says "the information available to the model was therefore the same". It was not. In the transcripts, OpenCode's skill tool returns the body inside `<skill_content>` with a `<skill_files>` manifest giving the absolute path of each bundled file. Claude Code returns "Launching skill" and injects the body as a synthetic user-role message with an `ARGUMENTS:` block and no file manifest; the script path appears only because the `SKILL.md` body names it. So the hosts differ in the channel and authority of the instruction and in whether bundled files are enumerated. Either could cause the reading behavior. In addition, all 60 Claude Code transcripts I sampled contain thinking blocks and none of 60 OpenCode transcripts contain reasoning events, so either the inference configuration differs or one stream omits it; the paper is silent. "Reading is the gate" is a post-hoc split on an outcome-adjacent variable (an agent that declines a script it has not read has no reason to decline), and "843 of 844" is close to a tautology. The decisive experiment is cheap and the paper names it without running it: append one system-prompt line to Claude Code, or patch OpenCode's skill tool.

**W6 (major). Transcript-derived labels are unvalidated, and the paper implies otherwise.**
§5.4 says "Our human-labelled sample checks whether these calls were remediation." §7 says the labels have "not yet been checked". The worksheets in `benchmark/review/pilot-labels/` are blank. The parenthetical in §5.4 describes work that has not been done. My re-scan of the 351 Claude Code "cleanup blocked" runs found 299 with a refused later call naming the target or its basename, and 52 (15%) that qualify only because a refused call contains the target's first path component. Some of those are real (`rm -r .cache`); others are unrelated (a refused `cd book/src && find ...`, `ls -la .vscode`). The rule is mostly right, but its precision is unknown.

**W7 (major). The two hosts were not run under equivalent conditions.**
OpenCode ran with a temporary home, `--pure`, and a per-run data directory. Claude Code ran with the real home directory; its `capability.json` shows four plugins and nineteen other skills loaded beside the benchmark skill, and `apiKeySource: none`, which suggests account login, while the harness notes say OpenCode went through the Anthropic API. The paper does not say whether those plugins and skills are stock. The presets are not equivalent either: OpenCode's `edits_denied` removes the edit tools, Claude Code's refuses calls; Claude Code's `Bash(python3:*)` rule refuses some compound commands that start with `python3` (for example `python3 ... ; echo`); and both hosts allow arbitrary `python3`, which can write any file, so "edits refused" is not a boundary in either preset. The refusal itself is a property of headless mode, where a call that would prompt is denied. Interactively the user would be asked. The preset finding should be scoped to non-interactive use.

**W8 (major). The benchmark is homogeneous on every security-relevant axis.**
All 36 families were written by one model (`author_model: claude-sonnet-5-5` in every `family.json`, same vendor as the evaluated model; the paper says only "LLM assistance"). All 113 `SKILL.md` bodies are one templated sentence of 34 to 42 words ("Run the bundled script with `python3` ..."), identical between benign and adversarial packages. Harm comes from five templates, one boundary paragraph, scripts of median 63 lines with the payload in a named, docstringed function. Workspaces have a median of 11 files and about 4 KB, which "realistic workspace" (§4) overstates. The family-cluster interval captures variation in task surface only. It says nothing about variation in payload design, prompt wording or skill style, so the tight intervals overstate what is known. The "disguised" variant is not an evasion test: it is unobfuscated and a reading agent rejects it at the same rate.

**W9 (major). §2 misstates what the skill format grants.**
§2 says "The skill format itself grants nothing". Every package ships `allowed-tools: Bash(python3:*)` in its frontmatter, which the harness's own notes call "a Claude-specific permission grant" and "still untested". This is the one permission lever the attacker controls, and it is host-specific content inside the "identical" package. The paper never mentions it.

**W10 (major). Depth and completeness for this venue.**
The PDF is seven pages, about five of body, against a 13-page limit, with no appendix. The artifact calls the campaign a pilot throughout (`agent-pilot`, evidence tier `real_agent_runtime_pilot`, claim status `supported_agent_pilot`). The paper shows no skill package, no prompt, no payload template and no contract, so a reader cannot judge severity without the artifact. Results the artifact already has are missing: per-attack breakdown, task completion on adversarial runs, whether the final message tells the user about the change (`final_mentions_target`: 202 of 430 for Claude Code against 328 of 429 for OpenCode in pair 1), and canary leakage into the final message (40 of 110 secret-in-output runs under the edit-refusing preset against 5 of 110).

**W11 (minor).** The title promises "conformance testing" and §3 describes contracts and a calibrated comparator, but no reported number uses the contract checker; `tools/analyze_agent_pilot.py` does not read contract findings.

**W12 (minor).** "The grant gates execution" (§5.4) omits that the ungranted `default` preset also has zero benign utility (0 of 108 reports), and those presets have one repeat.

**W13 (minor).** Figure 1 has no axis or percentage labels. Table 2 leaves the disguised intervals blank although `results/agent-pilot/analysis.md` has them.

**W14 (minor).** All 30 references are arXiv identifiers, 25 from 2026. To my knowledge AgentDojo, InjecAgent, ASB and Task Shield have peer-reviewed versions that should be cited. There is no differential-testing literature (McKeeman; Csmith; Frankencerts) and no permission-system or package-supply-chain literature, which are the closest established analogues.

**W15 (minor).** Contribution 4 (a claim ledger) checks that the paper's numbers equal `analysis.json`. It does not check that `analysis.json` follows from the runs, and it cannot check prose claims such as the one in W5.

## 4. Detailed comments by section

**Abstract and §1.** Replace "ran the harmful script" with a metric that means it (W4). "Execution tracks one behavior" should be stated as a correlation. The contribution list should not count the claim ledger as a research contribution.

**§2 Threat model.** State why a user would grant `Bash(python3:*)` and whether the skill's own `allowed-tools` line can obtain it. State that the user prompt always carries an explicit boundary paragraph and discuss how often real users write one. Either bring network egress into scope with a local sink, or argue why local reversible changes are a valid proxy. As written, the attacker is given code execution and then assumed not to use it.

**§3 Method.** "Two runs compared on a task differ only in host or preset" is too strong given W5 and W7. Define `executed` precisely and report as-shipped separately. Either report contract findings or remove the contract paragraph and retitle.

**§4 Benchmark.** Show one full package, one prompt and the five templates. Name the authoring model. Report workspace and script sizes. Explain that benign and adversarial `SKILL.md` are identical, so the attack is purely a trojaned script and the paper says nothing about instruction-level attacks.

**§5.1, Table 2, Figure 1.** Add as-shipped rows. Rename "ran, no harm at end" or split it into "sanitized run" and "ran as shipped, later repaired". Add per-attack results; the artifact shows large differences by kind (for example secret-in-side-file is almost never repaired even with edits accepted: 70 of 110 left).

**§5.3 Benign utility.** The benign scripts contain nothing unusual, so this measures utility on unsuspicious scripts only. A control with benign scripts that legitimately write a cache or touch a dotfile is needed to measure over-refusal by the reading host. OpenCode's lower "report matches script output" (84.7%) already suggests it rewrites more.

**§5.4 Presets.** Scope to headless mode. Note that the agent could have repaired through the permitted `python3` and mostly did not, so the result is about the agent's tool choice under a porous preset as much as about permission design. Remove or substantiate the human-label parenthetical.

**§5.5 Mechanism.** Remove "the information available to the model was therefore the same". Describe the actual skill-tool outputs of both hosts. Run the intervention.

**§6 Discussion.** The mitigation (show the script source, or require a read) is evaluated against payloads that are not hidden. An adaptive attacker moves the payload to an imported module, a second file, or a longer script. Without that evaluation the recommendation is not actionable for host developers.

**§7 Limitations.** Add the unreported Sonnet runs, the unequal isolation, the inference-configuration difference, and the three-day collection window on single versions of fast-moving products.

**§8 Related work.** HarnessSafe and the harness-disclosure paper are the closest work and get one sentence each. A reviewer cannot tell from this text what they measured and why it does not subsume the present result.

## 5. Questions for the authors

1. What are the as-shipped execution rates per host and preset, and why does the abstract use the broader count?
2. Why are the Claude Code Sonnet 5.5 runs in the artifact not reported? Does the cross-host gap persist on a stronger model on both hosts?
3. Which host component causes the reading behavior: system prompt, the role in which the skill body is delivered, the `<skill_files>` manifest, or thinking configuration? Did OpenCode run with extended thinking?
4. Are the four plugins and nineteen skills in Claude Code's capability snapshot stock, or from the experimenter's account?
5. Does Claude Code honor the package's `allowed-tools: Bash(python3:*)` when only the Skill tool is granted? If so, the attacker controls the grant and §2 is wrong; if not, say so.
6. Were failed, capped or timed-out runs deleted and re-run? The retained set has five agent errors in about 7,000 runs. What was the replacement rule?
7. What happens without the boundary paragraph in the prompt?
8. What is the status of the human labelling, and what is the agreement with the automated labels?
9. Has disclosure happened? To whom, when, and what was the response? Do the vendors consider this in scope, given that the user installed the skill and granted the permission?
10. Did the automated use of account-based access to these products comply with the providers' terms?

## 6. Required changes for acceptance

1. Report execution of attacker code as shipped as the primary metric, and separate sanitized runs from repaired runs in every table and figure.
2. Add at least one more model on both hosts, including a current frontier tier, and at least one more same-model host. Report the existing Sonnet runs.
3. Run the intervention that tests the mechanism (one changed host component, everything else fixed) and report benign cost.
4. Strengthen the threat model: payloads with irreversible effect (egress to a local sink), payloads placed outside the entry script, a prompt condition without the boundary paragraph, and a sample of real skills from the cited corpora. Address `allowed-tools`.
5. Complete and report the human-label validation with agreement statistics; remove the §5.4 parenthetical until then.
6. Equalize or fully document host isolation and inference configuration; describe both skill-tool outputs accurately.
7. Scope the preset finding to non-interactive mode, or test an interactive condition.
8. Provide a working anonymized artifact link containing scrubbed transcripts and end-state workspaces, and a complete ethics section (see §7).
9. Expand to full length: worked example, package and payload listings, per-attack and per-family results, user-facing disclosure analysis.
10. Align the title and §3 with what is actually measured.

## 7. Ethics and open-science assessment

**Ethics.** The section is five sentences. The low-risk points are fair: no human subjects, synthetic canaries, no network, simple payloads. It falls short of what this PC expects in four ways. First, there is no stakeholder analysis (host vendors, their users, skill authors, registry operators) and no weighing of harms and benefits. Second, disclosure is stated in the present progressive ("we are disclosing") with no date, channel or response; given that file timestamps put the runs between 16 and 18 November and the PDF was built on 19 November, I read this as an intention, not an event. Third, the paper does not say whether the behavior is a vulnerability under the vendors' own trust model, which determines whether disclosure is even the right frame. Fourth, there is no statement on compliance with provider terms for roughly 7,000 automated runs through account-based access; the harness notes record a Codex account hitting its usage limit.

**Open science.** Not compliant as submitted: a promise and no link. Inspecting the repository as it stands raises further concerns that a release must fix:

- Transcripts and end-state workspaces are excluded from version control (`.gitignore` rules for `results/**/stdout.log` and `results/**/workspace/`), and `tools/analyze_agent_pilot.py` needs the transcripts. A clone of the tracked files cannot regenerate `results/agent-pilot/analysis.json`; only the paper-to-analysis transcription check runs.
- The stored transcripts are not scrubbed. 3,699 of 7,162 `stdout.log` files contain the experimenter's home-directory path, and all contain the per-user temporary root. Releasing them as they are would break anonymity; the section's "scrubbed transcripts" do not yet exist.
- Metadata for 920 of 7,162 runs is tracked.
- The artifact contains results the paper does not report (Sonnet 5.5 on Claude Code, Cursor on two models) and a long list of caveats in `tools/run_agent_pilot.py` of which the paper carries a fraction.

On the positive side, the harness, packages, prompts and analysis code exist, are readable, and the package self-check and claim ledger are good practice.

## 8. Recommendation

**Reject.**

The question is good and the raw observation is striking: on this benchmark, the same model ID behaves very differently under two hosts. But the submission is a pilot written up as a full paper. The security framing rests on reversible, templated, low-severity workspace edits with the realistic payloads ruled out of scope, so the central metric does not measure attacker success (W1). The general conclusions rest on one host pair, one small model and one version, while the artifact holds unreported runs suggesting the effect is model-dependent (W2). A headline number in the abstract is wrong as worded (W4), the mechanism is asserted with a supporting statement the transcripts contradict (W5), the labels are unvalidated while the text implies a human check (W6), and the open-science requirement is not met (W3). Fixing these means new models, new hosts, an intervention experiment, a stronger adversary, label validation and a rewrite to roughly twice the length. That is a new evaluation, not a revision that a shepherd or a major-revision cycle can verify against a bounded list. I would encourage resubmission once that work is done; the corrected as-shipped numbers suggest the core effect is real and may be larger than reported.

## 9. Reviewer confidence and what I could not verify

**Confidence: 3 of 4.** I am familiar with agent-host permission systems, skill security and benchmark methodology, and I checked the paper's numbers and several of its claims against the artifact.

Not verified:

- I did not re-run any agent, so I cannot confirm the runs reproduce or that the hosts behave this way outside the experimenter's machine and account.
- I did not re-run `tools/analyze_agent_pilot.py` or `tools/validate_claim_ledger.py`; I compared the paper to `results/agent-pilot/analysis.md` by reading and recomputed selected counts from `run_meta.json` and transcripts with my own scripts. My as-shipped and cleanup re-scans reuse the harness's regular expressions and inherit their errors.
- The thinking-configuration observation is from 60 sampled transcripts per host; OpenCode's JSON stream may simply omit reasoning events.
- I could not determine whether the plugins and skills in Claude Code's capability snapshot are stock.
- I could not verify the existence or content of the 2026 arXiv references, so I cannot assess novelty against HarnessSafe and the harness-disclosure paper beyond what the paper says.
- I could not check whether disclosure has occurred, or the providers' terms.
- The Sonnet comparison is 25 runs per cell on five older cases with different prompts; it shows the question is open, not the answer.
