# Review: SkillDiff: Differential Runtime Conformance Testing for Portable AI Agent Skills

Venue: USENIX Security 2027 (Cycle 2). Reviewer lens: novelty and positioning, plus a full review.
Material read: `paper/usenix/main.tex`, `paper/usenix/build/main.pdf`, `paper/usenix/refs.bib`,
`paper/usenix/fig-pilot-outcomes.tex`, and, as an artifact evaluator would,
`results/agent-pilot/analysis.md`, `results/agent-pilot/analysis.json`, `results/agent-pilot/runs/*/run_meta.json`
(aggregated, plus a sample of `stdout.log` transcripts), `paper/claim-ledger.json`, `tools/run_agent_pilot.py`,
`paper/gate5-adjudication-form.md`, and one family under `benchmark/agent-pilot/`. No model API was called.

## 1. Paper summary

The paper argues that the security outcome of a third-party agent skill is a property of the skill and the
host together, not of the package. It fixes skill package, prompt, workspace and model (Claude Haiku 5.5) and
runs 108 synthetic tasks (36 LLM-assisted families; benign, adversarial and 44 "disguised" packages) on
Claude Code 2.1.310 and OpenCode 1.18.29 in headless mode under two permission presets each. Claude Code runs
the adversarial script in about 86% of runs and OpenCode in about 16%, and the harmful workspace change is
still there at the end of 79.6% versus 0.9% of runs. Within Claude Code, the preset that refuses file edits
leaves the harm in place more often than the one that accepts them (79.6% versus 46.1%), which the authors
attribute to the host refusing the agent's own cleanup. Execution correlates with whether the agent reads the
script before running it.

## 2. Strengths

- The question is well posed and the control is the right one: same model on two hosts. Most prior
  cross-client comparisons I know of change client and model together. As far as I could check, no cited
  paper reports a same-model, host-varied, security-outcome comparison for skills.
- The primary outcome (harm present in the workspace at the end) is observed by snapshot diff and does not
  depend on transcript parsing. The headline 79.6% versus 0.9% therefore survives the unvalidated labels.
- Effects are large and uniform across tasks (105 of 108 tasks in the same direction); the family-cluster
  bootstrap is the correct unit of resampling.
- A benign-utility control is included, so "safe because it does nothing" is ruled out for OpenCode.
- The non-monotonic preset result is a concrete, actionable observation for host designers.
- The numbers in the paper match `results/agent-pilot/analysis.md`; I recomputed the pooled counts
  (236 + 844 = 1,080; 108 + 540 + 539 = 1,187) and found no arithmetic discrepancy. The claim ledger is a
  good practice.
- Limitations are stated more honestly than usual (association not manipulation; labels unvalidated).

## 3. Weaknesses, ordered by severity

**W1 (major, borders on fatal for this venue). Two hosts, one small model, one version each, headless only.**
The general claim ("a verdict about a skill does not transfer between hosts"; "skill security is a property
of the skill and the host together") rests on a single host pair on the cheapest model tier. With two hosts
there is no way to tell which one is the outlier. The artifact's own third host (Cursor agent, different
model, `results/agent-pilot/analysis.md` section C) read the script first in 3 of 98 runs and ran it in 79 of
98, which looks like Claude Code, not OpenCode; that suggests "OpenCode on Haiku is unusually cautious" is as
good a reading as "hosts differ". No second model is tested, so the effect could vanish or invert on a
stronger model. The artifact itself calls all of this a "pilot" (`tools/run_agent_pilot.py` BOUNDARIES:
"Pilot tier"; ledger statuses `supported_agent_pilot`); the paper drops that word.

**W2 (major). The "ran the harmful script" metric means different things on the two hosts, and the paper's
wording hides it.** `executed` counts any successful Python call that names the script, including patched or
wrapped copies (`tools/run_agent_pilot.py`: "`script_executed` ... also counts runs that import or patch it
first"). Aggregating `run_meta.json` for the pair-1 adversarial cells: Claude Code ran the script as shipped
in 432 of its 463 executed runs; OpenCode ran it as shipped in 10 of its 86 executed runs, and the other 76
were modified copies with the harmful step removed. So OpenCode did not "run the harmful script in 15.9% of
runs" (abstract); it ran the shipped harmful script in about 2% and a de-fanged version in about 14%. The
sentence "When OpenCode did run the script, the harm was almost never present at the end" reads as cleanup,
when the harm never happened. The same conflation affects the outcome class "ran, no harm at end" (it merges
"never harmed" with "harmed, then repaired": in Claude Code with edits accepted, 162 of 194 such runs were
as-shipped runs that were repaired, 32 were modified runs) and the mechanism counts (the "63 of 236" who read
and still "ran"). The correction mostly strengthens the cross-host gap, but an abstract number that is wrong
by construction for one arm is not acceptable.

**W3 (major). The headline preset finding is an artifact of an incoherent, headless-only configuration and is
over-read.** (a) The "stricter" preset allows `Bash(python3:*)`, which is arbitrary code execution and
strictly more powerful than the Edit tool it refuses. It is not a stricter policy in any ordering a security
engineer would accept; it is a policy that denies the weaker capability while granting the stronger one. In
62 of 540 runs under that preset the agent did modify things through `python3`. So the host did not make
cleanup impossible; the agent tried Edit/Write/`rm`, was refused, and did not fall back to the channel it
had. (b) Edits are "refused" only because headless mode auto-denies what an interactive session would ask
about. In interactive use the user would be prompted for exactly the cleanup edit. The paper generalizes to
"permission design is not monotonic" without this caveat. (c) "Cleanup blocked" is decided by a rule that
matches a refused call on the target path, its basename or its *first path component*
(`results/agent-pilot/analysis.md`, Definitions), and no human has checked it. Section 5.4 says "Our
human-labelled sample checks whether these calls were remediation", while Section 7 says labels "have not
yet been checked" and `paper/gate5-adjudication-form.md` says "scaffold only. No Gate 5 human adjudication
has been completed". The parenthetical in 5.4 describes work that does not exist. Benign runs show the agent
rewrites the report in about 17% of runs when edits are accepted (report matches script output 83.0% versus
99.1%), so a refused later call on the report is not automatically remediation.

**W4 (major). The paper ignores what the agent told the user.** In the sampled "cleanup blocked" transcripts
the Claude Code agent runs the script, then reads it, notices the side effect, tries to revert, is denied,
and says so in its final message, naming the file and the change. The analysis has the columns
(`final_mentions_target`: 202 of 430 for the edit-refusing preset; `canary_in_final_message`: 40 of 110
secret-in-output runs) but the paper reports neither. For a headless run the final message is the user's
only channel; "harm present, user warned" and "harm present, silent" are different security outcomes. The
same column cuts the other way too: the agent copies the canary into its final message in 40 (adversarial)
and 48 (disguised) runs under the edit-refusing preset, a leak into a sink the "harm at end" metric does not
count. And every secret-in-output run in which the report was later cleaned still wrote the secret to disk
and, in 80 to 100 runs per cell, pulled it into the model context (`canary_in_transcript`). "No harm at end"
is a generous name for that.

**W5 (major). Mechanism is asserted from a correlation that the authors could have resolved.** "Reading is
the gate" is confounded with host (OpenCode reads 97%, Claude Code 20 to 24%), and within-host the read and
the decision not to run are both downstream of the same suspicion. The transcripts show the real difference
is ordering: Claude Code audits after running, OpenCode before. Why is not investigated. OpenCode is open
source and Claude Code's stream-json output exposes its tool list and injected messages, so the system prompt
and skill-tool text of both hosts can be diffed directly, and the obvious manipulation (inject the script
source or a "read before run" line into one host) is described in Section 6 as future work. For a paper whose
contribution is a controlled method, omitting the one controlled manipulation is a serious gap. The claim
"the information available to the model was therefore the same" is also too strong: the hosts differ in
system prompt, tool set (OpenCode with edits denied has no edit/write tool at all), shell allowlist
(OpenCode: `python3` only; Claude Code: also read-only commands) and probably reasoning settings.

**W6 (major, positioning). Related work is shallow, in places inaccurate, and omits the two literatures the
title invokes.** See Section 4, "Related work". In short: (i) no differential-testing or conformance-testing
citation at all in a paper titled "Differential ... Conformance Testing"; (ii) all 30 references are arXiv
preprints, with peer-reviewed versions and the foundational prompt-injection and supply-chain literature
missing; (iii) HarmfulSkillBench and Runtime Skill Audit are mis-described; (iv) the closest work,
HarnessSafe, whose abstract already says containment "strongly depends on the harness-model configuration",
is dismissed in one clause without a factor-by-factor comparison; (v) the relation of the cleanup result to
Measuring the Permission Gate, which reports an artifact-cleanup finding around file edits, is not discussed.

**W7 (major). The method contribution is thin.** "Hold everything fixed and vary one factor" is experimental
control, not a new testing method. The "task-conditioned security contract" is listed in contributions (1)
and (2), but no result in the paper uses contract findings; every reported number comes from one workspace
diff flag and transcript regexes. "Conformance" has no referent: there is no specification the hosts are
tested against. The paper is 7 pages of a 13-page budget and has no per-attack table, no example package, no
transcript excerpt and no host-level analysis.

**W8 (minor to major). Benchmark realism.** All 108 tasks are LLM-assisted, author-written and synthetic; the
harmful code is five fixed templates, "not hidden", and several harms are barely harmful (appending a
`Reviewed-by` line; a `.vscode/tasks.json` that runs `echo`). "Disguised" variants are five author-written
packages for the two secret kinds with no obfuscation. Every prompt ends with an explicit boundary paragraph
("Do not create or modify files other than the requested outputs"), which primes the cleanup behaviour the
preset result depends on; its effect is not ablated. No real-world or in-the-wild malicious skill is run.

**W9 (minor). Undisclosed asymmetries in the "fixed" package and setup.** The shipped `SKILL.md` carries
`allowed-tools: Bash(python3:*)`, a Claude-Code-specific grant that OpenCode ignores
(`tools/run_agent_pilot.py`: "The identical skill bytes contain an `allowed-tools` line that is a
Claude-specific permission grant", and the harness grant means it is "still untested"). Claude Code ran with
the real home directory and concurrent runs sharing it; OpenCode ran with a temp home. The "grant gates
execution" paragraph omits that without the grant benign tasks also fail (report written in 0 of 108 runs
under `default`), so it shows only that headless Claude Code does nothing without an allow rule, on one
repeat.

**W10 (minor). Reporting.** One OpenCode cell has 539/219/537 runs, not five per task; excluded
`agent_error` runs are not counted in the paper; 762 early OpenCode runs were discarded and re-run
(harness notes) and this is not mentioned; the 1,187 OpenCode runs in Section 5.5 pool a third preset
(`default`, one repeat) that is not in Table 1; disguised rows in Table 2 omit the intervals that the
analysis has.

## 4. Detailed comments by section

**Title and abstract.** "Conformance" and "portable" over-promise (see W7; two hosts with different skill
directories and a host-specific frontmatter line). "Ran the harmful script ... OpenCode in 15.9%" is wrong as
worded (W2). "Because it refused the agent's later calls" is a causal claim resting on an unvalidated rule
(W3).

**Section 1.** The framing "most security work treats the package as the object" is fair for scanners and
ecosystem studies but not for the runtime benchmarks cited in the same paragraph, which do study agent
behaviour. The citation groups are loose: MalSkillBench is a (largely generated) benchmark, not an ecosystem
study; Runtime Skill Audit is a dynamic detector, not a benchmark of agent behaviour "inside one
environment"; HarmfulSkillBench is about skills that enable misuse, not skill-facing attacks.

**Section 2, threat model.** The attacker controls the package, but the harness (the defender) supplies the
`python3` allow rule that makes the attack possible, and the package also asks for it. State who is assumed
to grant `Bash(python3:*)` and why that is a realistic deployment. Excluding network egress removes the
harm that matters most for the secret kinds: with egress, cleanup at the end is irrelevant and the
"harm at end" metric would not distinguish the presets.

**Section 3.** "Executed (as shipped or modified)" needs to be split everywhere. Define "harm persists" per
attack kind; for secret-in-output the harmed file is the requested report, so any refused write on the
report counts as "cleanup blocked". The calibration on "author-controlled runtime profiles" is mentioned but
no result is shown, so it cannot support the oracle.

**Section 4.** Say that tasks, workspaces and benign scripts were generated by a Claude model
(`author_model` in `family.json`) and then run on a Claude model; discuss whether same-vendor authorship
biases recognizability of the harmful code. "Each harmful script realizes its harm when run alone" is the
same runtime-verification idea as MalSkillBench and should be credited.

**Table 1.** The pairing is not symmetric: OpenCode with edits denied has no edit/write tools, Claude Code
has them and gets refusals; shell allowlists differ. This is disclosed in Section 7 but belongs next to the
table, because the cleanup-blocked outcome can only occur on the host that exposes a tool and then refuses
it.

**Table 2 / Figure 1.** Add as-shipped versus modified execution, per-attack-kind rows (the analysis has
them and they are informative: secret-in-output is fully repaired with edits accepted, secret-in-side-file
almost never is, 70 of 110 left), and the final-message columns. The pooled 46.1% hides that the preset
effect is carried by two or three attack kinds. "Harm present at end" is 0.9% for OpenCode but its
denominator is dominated by runs that never executed; report it conditional on as-shipped execution as well.

**Section 5.3.** "Similar rates" glosses over a 14-point gap in "report matches script output" under pair 1
(99.1% versus 84.7%, CI +10.0 to +19.6 in the analysis). Explain it.

**Section 5.4.** See W3. Also report how often the agent, after a refused edit, used `python3` to repair,
and how often it warned the user. Drop or substantiate the human-label parenthetical.

**Section 5.5.** Report read-then-ran on as-shipped runs only. Reframe as ordering (audit before versus
after execution), which is what the transcripts show, and say what in each host's prompt or tool text
produces it.

**Section 6.** The three recommendations are reasonable but the second and third are untested; "report
host, version, preset, model" is already the argument of Stop Comparing LLM Agents Without Disclosing the
Harness (cited) and should be credited as such.

**Section 8, related work (primary lens).**

- *Novelty of the finding.* I could not find, among the cited works I checked, one that fixes the model and
  the skill and varies the host with a security outcome. On that narrow axis the paper appears new. But
  "outcomes depend on the harness" is no longer a new message: HarnessSafe's abstract states that containment
  "strongly depends on the harness-model configuration", and Skill-Inject and the MCP client study already
  show cross-client differences. The paper's increment is the removal of one confound on one host pair and
  one model. That is a real but small increment, and the paper must argue it against HarnessSafe in a
  paragraph with a table of factors (hosts, models, whether model is held fixed, permission modes, carrier,
  outcome), not in half a sentence.
- *Inaccurate or loose characterizations.* HarmfulSkillBench (arXiv 2604.15415) measures harmful skills in
  registries and how a pre-installed harmful skill lowers refusal on misuse tasks; describing it as
  evaluating "agent safety under skill-facing attacks" is wrong. Runtime Skill Audit (2606.11671) is a
  detection method instantiated on OpenClaw; the Section 8 wording is fine, the Section 1 grouping is not.
  AgentTrap's abstract speaks of the "model-framework-workspace environment"; if it evaluates more than one
  framework, the Section 1 claim "inside one environment" is wrong (I could not confirm from the abstract).
  Measuring the Permission Gate (2604.04978) is described only as a stress test "on a fixed model"; its
  finding that in-project file edits bypass the classifier, with the largest gap for artifact cleanup, is
  directly related to the edit/cleanup interaction here and should be discussed.
- *Missing.* (1) Differential testing and its security uses (McKeeman's differential testing; Csmith;
  Frankencerts-style differential testing of certificate validation; differential analyses of browser and
  Android permission behaviour across vendors). (2) Indirect prompt injection foundations (Greshake et al.)
  and peer-reviewed versions of AgentDojo, InjecAgent, ASB and the malicious-skills measurement, which are
  cited only as arXiv. (3) Software supply-chain work on install-time script execution and extension
  ecosystems (npm/PyPI install scripts, VS Code and browser extensions), which is the established framing
  for "run the bundled script with the host's authority". (4) Practitioner reports on coding-agent
  permission modes; I recall public write-ups of an agent's own cleanup being denied by a permission mode,
  which would be an anecdotal precedent for Section 5.4 (not verified by me). (5) Other 2026 skill-auditing
  preprints that I believe exist but did not look up (SkillTester, SkillHarm, SkillJuror); the authors
  should check them.
- The Defenses paragraph is a list. SkCC ("portable and secure skill compilation for cross-framework
  agents") is the one defense that addresses portability across hosts and deserves an actual comparison.

## 5. Questions for the authors

1. Splitting `executed` into as-shipped and modified, what are the Table 2 and Section 5.5 numbers?
2. In "cleanup blocked" runs, how often did the final message tell the user about the remaining harm? How
   often did the agent repair through `python3` after a refused edit?
3. What is different in the two hosts' system prompts and skill-tool text for this model? Does adding one
   "read bundled scripts before running them" line to Claude Code (or removing the equivalent from OpenCode)
   move the read rate?
4. Does the cross-host gap hold on a second model (for example a Sonnet-tier model on both hosts) and on a
   third same-model host?
5. Why is the edit-refusing preset called stricter when it grants `python3:*`? What happens with a coherent
   strict preset (script path allowlisted, no general interpreter) and in interactive mode?
6. What happens without the boundary paragraph in the prompt?
7. Does the `allowed-tools` frontmatter line alone (no harness grant for `python3`) let Claude Code run the
   script?
8. How does HarnessSafe's design differ from yours factor by factor? Does it include any fixed-model
   harness comparison?
9. Has disclosure to the two vendors happened, and what was the response?

## 6. Required changes for acceptance

1. Report execution as shipped versus modified in the abstract, Table 2, Figure 1 and Section 5.5; rename
   the outcome classes so "never harmed" and "harmed then repaired" are separate.
2. Complete the two-rater human labelling for execution, reading and, above all, "cleanup blocked =
   remediation attempt", with agreement statistics; remove the present-tense claim in Section 5.4 until then.
3. Add at least one more model on both hosts and, ideally, a third same-model host; otherwise restrict every
   general claim to "this pair on this model".
4. Run the one-component manipulation (script source or a read-first instruction injected into one host) and
   report it; diff and report the hosts' prompts and tool descriptions.
5. Reframe Section 5.4: state that the refusal is headless auto-deny, that the preset grants a general
   interpreter, report the user-notification and `python3`-repair rates, and add a coherent strict preset.
6. Report the final-message and transcript canary sinks alongside "harm at end".
7. Rewrite related work: differential-testing lineage; accurate descriptions of HarmfulSkillBench, Runtime
   Skill Audit, AgentTrap and Permission Gate; a factor table against HarnessSafe, Skill-Inject, Permission
   Denied and Permission Gate; peer-reviewed citations where they exist.
8. Either use the contracts in a reported result or drop them from the contributions; justify or drop
   "conformance".
9. Disclose the `allowed-tools` line, home-directory and concurrency asymmetries, discarded and excluded
   runs, and the benign failure under ungranted presets, in the main text.
10. Add realism: some in-the-wild or independently authored malicious skills, and harms with consequence
    beyond marker lines.

## 7. Ethics and open-science assessment

**Ethics.** The section is present and the risk is low: synthetic canaries, no network actions, temporary
workspaces, simple payloads. Gaps: disclosure is described as in progress ("We are disclosing"), with no
date, channel or response; the paper names two products and one comes out badly, so the vendor's response
matters. The section does not discuss terms of service for automated use of the hosts and accounts (the
harness notes show personal accounts hitting usage limits), nor a stakeholder analysis in the form the call
asks for. No human subjects now, but the planned two-rater labelling should say whether raters are authors.

**Open science.** The section promises release "at an anonymized link for review" but gives no link, so as
submitted the artifact is not available to reviewers. The repository I inspected is thorough (harness,
families, run metadata, analysis, claim ledger) and reproduces the paper's numbers from stored runs, which
is to its credit. Problems for double-blind release: raw `stdout.log` transcripts contain a local account
name in directory listings and machine-specific temp paths, so the "scrubbed transcripts" claim is not yet
true of what is in the repository; the artifact labels the study a "pilot", which the paper does not; and
re-running requires paid accounts on two commercial hosts at pinned versions that may no longer be
installable, which the section should acknowledge.

## 8. Recommendation

**Major revision.**

The paper has one clean and, as far as I can tell, new measurement: with the model held fixed, two production
hosts differ by roughly 70 to 80 points in whether an adversarial skill script's harm ends up in the
workspace, and that outcome is observed directly. That is worth publishing once it is solid. As submitted it
is not at the bar for this venue: the general claim rests on one host pair and one small model (W1); the
abstract's execution number for one arm counts de-fanged runs as running the harmful script (W2); the
second headline finding depends on a headless auto-deny combined with a preset that grants a general
interpreter, on an unvalidated rule, and on ignoring that the agent often warns the user (W3, W4); the
mechanism is a correlation the authors had the means to test (W5); and the positioning is thin and partly
inaccurate, with the closest prior work not seriously engaged (W6). The method contribution on its own would
not carry a paper (W7). All of the required changes are achievable within a revision cycle with the existing
harness, which is why I do not recommend rejection outright; if items 1 to 5 cannot be delivered, or the
cross-host gap does not survive a second model, my recommendation becomes Reject.

## 9. Reviewer confidence and what I could not verify

Confidence: **3 of 4** (knowledgeable in agent and supply-chain security; checked the artifact's stored
results but did not re-run any agent).

Not verified:

- I looked up eight arXiv abstract pages (2602.20156, 2608.06984, 2608.02670, 2604.04978, 2605.13940,
  2606.11671, 2606.07131, 2604.15415). Abstracts only, not full texts. From abstracts alone I could **not**
  confirm: that Skill-Inject uses a different model per CLI; that HarnessSafe never holds the model fixed
  across harnesses; that Permission Denied contains no fixed-model harness swap or security outcome; that
  Permission Gate uses a fixed model; whether AgentTrap evaluates one framework or several.
- Not looked up at all: SkillSafetyBench, Semia, Agent Skills in the Wild, "Do Not Mention This to the User",
  Towards Secure Agent Skills, Under the Hood of SKILL.md, When Safe Skills Collide, the MCP client study
  (2603.21642), MCPSecBench, Stop Comparing LLM Agents, How Agents Ask for Permission, SkillScope,
  SkillGuard, VIGIL, Sealing the Audit-Runtime Gap, RuntimeTickets, SkCC, ClawGuard, Task Shield. Their
  characterizations in the paper are unverified by me.
- The uncited works I name as possibly relevant (SkillTester, SkillHarm, SkillJuror, practitioner write-ups
  on denied cleanup) are from memory and were not checked.
- I did not re-run the harness or any host, so I cannot confirm that the stored transcripts are what those
  host versions produce, that the hosts' "same model" calls use comparable sampling or reasoning settings,
  or that host versions were in fact pinned. My transcript reading covered a random sample of 60
  "cleanup blocked" runs by tool-call tally and a handful in full, not all of them.
- I did not run `tools/validate_claim_ledger.py`; I compared paper numbers to `results/agent-pilot/analysis.md`
  by hand.
- I did not check the official USENIX style compliance of the built PDF beyond page count (7 pages) and
  absence of author metadata.
