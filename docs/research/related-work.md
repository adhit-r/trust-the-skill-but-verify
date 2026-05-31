# Related Work and Differentiation

This note supports `RM-02` in `research-roadmap.md`. It is a
source-checked positioning artifact for the SkillDiff paper draft, not a new
experiment artifact.

Source check: primary sources refreshed on 2026-05-28. Before submission, rerun
this check against current paper versions, official specifications, and official
project pages.

Boundary statement: This refresh is a positioning artifact; it does not add
experiment evidence, prevalence claims, Semia equivalence, live guardrail
efficacy, completed human/manual review, public-network exfiltration evidence,
commercial-runtime coverage, or defense-success evidence.

## Core Position

Recent work establishes that agent skills, skill files, MCP servers, and
tool-using agents are security-relevant surfaces. SkillDiff asks a narrower
runtime-conformance question:

> Given the same skill, task, contract, workspace snapshot, prompt, variant,
> and repeat identity, does changing only the runtime profile change observed
> file, shell, network, tool, approval, persistence, context, cleanup, and
> canary behavior?

The current draft should avoid firstness claims. The defensible novelty
sentence is:

> SkillDiff fixes the skill/task/contract/workspace/prompt/variant/repeat
> invariant and varies runtime profile to measure security conformance drift.

## Source-Checked Map

| Layer | Primary source | What it studies | SkillDiff boundary |
| --- | --- | --- | --- |
| Static skill auditing | [Semia: Auditing Agent Skills via Constraint-Guided Representation Synthesis](https://arxiv.org/abs/2605.00314) | Converts skill artifacts into a structured representation and checks semantic security properties with reachability-style queries. | Semia is a static auditor. SkillDiff does not claim Semia equivalence; the local Semia-style baseline is an approximation only. |
| Skill-facing safety benchmark | [SkillSafetyBench: Evaluating Agent Safety under Skill-Facing Attack Surfaces](https://arxiv.org/abs/2605.12015) | Evaluates skill-mediated safety failures where unsafe influence comes from skills, local artifacts, or execution-environment files. | SkillSafetyBench evaluates unsafe behavior under skill-facing attacks. SkillDiff compares runtime-profile conformance for fixed triples. |
| Harmful-skill measurement | [HarmfulSkillBench: How Do Harmful Skills Weaponize Your Agents?](https://arxiv.org/abs/2604.15415) | Measures harmful skills in public ecosystems and builds harmful-skill benchmark cases. | HarmfulSkillBench studies harmful capability and refusal behavior. SkillDiff treats harmful or adversarial tasks as possible stressors, not prevalence evidence. |
| Skill poisoning detection | [RouteGuard: Internal-Signal Detection of Skill Poisoning in LLM Agents](https://arxiv.org/abs/2604.22888) | Detects poisoned skills before execution using internal response-time signals. | RouteGuard is a pre-execution detector. SkillDiff starts from a fixed selected skill and measures post-selection runtime behavior. |
| MCP trust calibration | [MCPShield: A Security Cognition Layer for Adaptive Trust Calibration in Model Context Protocol Agents](https://arxiv.org/abs/2602.14281) | Adds an MCP-specific security cognition layer around tool invocation and history. | MCPShield is a defense layer for MCP tool invocation. SkillDiff can use MCP-like fixtures as runtime surfaces but does not claim live MCPShield reproduction. |
| Remote MCP authentication measurement | [A First Measurement Study on Authentication Security in Real-World Remote MCP Servers](https://arxiv.org/abs/2605.22333) | Measures authentication and OAuth security in real-world remote MCP servers. | This motivates remote MCP risk, but SkillDiff's current MCP evidence is a bounded local fixture with no live remote-server or public-network claim. |
| MCP protocol semantics | [Model Context Protocol specification, 2025-11-25](https://modelcontextprotocol.io/specification/2025-11-25/basic) and [MCP Security Best Practices](https://modelcontextprotocol.io/docs/tutorials/security/security_best_practices) | Defines MCP protocol components, authorization, tools, resources, roots, and security guidance. | SkillDiff uses MCP/tool behavior as a runtime-profile dimension; it does not claim conformance coverage for every MCP client or server. |
| MCP practitioner taxonomy | [OWASP MCP Top 10](https://owasp.org/www-project-mcp-top-10/) | Practitioner-facing list of MCP-related risks and mitigations. | Useful checklist input for threat modeling; not experimental evidence for SkillDiff. |
| Agentic skill practitioner taxonomy | [OWASP Agentic Skills Top 10](https://owasp.org/www-project-agentic-skills-top-10/) | Practitioner-facing risks and mitigations for agentic skills across major agent platforms. | Useful checklist input for benchmark categories and artifact hygiene; not a substitute for trace-backed conformance evidence. |

## Additional Close Work

| Layer | Primary source | Relevance | Boundary |
| --- | --- | --- | --- |
| Skill ecosystem vulnerability scanning | [Agent Skills in the Wild](https://arxiv.org/abs/2601.10338) | Large-scale public-skill vulnerability measurement and taxonomy. | SkillDiff does not make ecosystem prevalence claims. |
| Malicious-skill corpus construction | [Malicious Agent Skills in the Wild](https://arxiv.org/abs/2602.06547) | Malicious-skill labeling and behavioral verification. | Malicious skills can inspire stressors, but SkillDiff is not a malicious-skill corpus. |
| Skill-file injection | [Skill-Inject](https://arxiv.org/abs/2602.20156) | Skill-file prompt-injection benchmark. | SkillDiff can include injected or adversarial variants, but its unit is runtime-pair conformance. |
| Task-conditioned least privilege | [SkillScope](https://arxiv.org/abs/2605.05868) | Identifies and constrains over-privileged skill actions for a task. | Least privilege is a baseline or mitigation in SkillDiff, not the main measurement question. |
| Skill discovery, selection, and governance | [Under the Hood of SKILL.md](https://arxiv.org/abs/2605.11418) | Shows `SKILL.md` content can manipulate discovery, selection, and governance. | SkillDiff begins after selection and asks whether runtime execution preserves the security contract. |
| Cross-framework skill compilation | [SkCC](https://arxiv.org/abs/2605.03353) | Compiles skills through a typed intermediate representation. | Compilation is upstream of SkillDiff; deployment-time runtime policy can still change behavior. |
| Model-in-skill backdoors | [BadSkill](https://arxiv.org/abs/2604.09378) | Studies backdoors hidden in skill-bundled learned artifacts. | SkillDiff can report bundled-resource behavior, but current claims do not cover broad backdoor detection. |
| Skill routing | [SkillRouter](https://arxiv.org/abs/2603.22455) | Studies skill selection and routing. | Routing affects activation, but SkillDiff's current invariant fixes the selected skill/task/contract triple. |
| Tool-call guardrails | [ClawGuard](https://arxiv.org/abs/2604.11790) | Runtime guardrail for tool-augmented agents under indirect prompt injection. | ClawGuard-style checks are a related baseline; local action-boundary checks are bounded approximations only. |
| Task alignment guardrail | [The Task Shield](https://arxiv.org/abs/2412.16682) | Checks whether agent actions serve user objectives. | Related to action-boundary relevance; SkillDiff does not reproduce Task Shield. |
| Agent security benchmarks | [Agent Security Bench](https://arxiv.org/abs/2410.02644), [InjecAgent](https://arxiv.org/abs/2403.02691), and [AgentDojo](https://agentdojo.spylab.ai/) | Benchmark attacks and defenses for tool-using agents. | Broader agent-security benchmarks evaluate attack success; SkillDiff evaluates runtime-pair conformance under fixed skill inputs. |

## Why Static Scanning Is Not Enough

Static scanning is necessary but incomplete for this paper's question because it
treats the skill package as the main security object. Runtime-induced drift
appears only when the same artifact is loaded under a host policy. The same
skill can observe different filesystem roots, approval prompts, shell access,
network defaults, MCP/tool visibility, persistence behavior, cleanup behavior,
and trace coverage depending on the runtime profile.

This is why the local scanner, reachability approximation, least-privilege, and
action-boundary artifacts must stay labeled as baselines or mitigations. They
cannot by themselves prove runtime conformance.

## Why Least Privilege Is A Baseline

Least privilege asks whether an action exceeds the authority required by a
task. SkillDiff also measures activation drift, approval drift, data-flow drift,
side-effect drift, cleanup drift, traceability gaps, and utility cost under
the same contract. A least-privilege policy can reduce risk inside the
experiment, but the measurement target remains runtime-profile disagreement.

## Why MCP Work Is Complementary

MCP security work is closest when skills invoke tools through MCP-connected
hosts. MCP papers and specifications study authorization, tool metadata,
server/client trust, tool invocation, sampling, resources, roots, and security
guidance. SkillDiff uses those ideas to define runtime surfaces and fixtures.

The current SkillDiff artifact does not claim external MCP server behavior,
remote MCP authentication coverage, packet capture, public-network evidence, or
commercial MCP-client behavior. Its current MCP evidence remains bounded local
fixture evidence unless future traces explicitly promote a broader execution
level.

## Drift Is Not Automatically A Failure

SkillDiff separates three outcomes:

- Contract violation: a denied event realizes outside the security contract.
- Attempted overreach: a denied action is attempted but blocked, denied, or
  fails before exposure or side effect.
- Runtime-pair disagreement: two runtime profiles produce different
  security-relevant traces for the same invariant.

This distinction prevents the paper from treating every behavioral difference
as a vulnerability. A stricter runtime that blocks a risky action can be a
valuable disagreement, but it is not automatically evidence of defense success
until utility cost, coverage, and repeat evidence support that claim.

## Related-Work Paragraph Draft

Recent work establishes that agent skills are an important security surface.
Static and semantic auditors such as Semia, ecosystem measurements such as
Agent Skills in the Wild and Malicious Agent Skills in the Wild, skill-facing
benchmarks such as SkillSafetyBench and HarmfulSkillBench, poisoning studies
such as Skill-Inject and RouteGuard, and governance work such as Under the Hood
of SKILL.md study skill content, skill selection, harmful capabilities, or
pre-execution detection. SkillScope and action-boundary defenses study
task-conditioned privilege and tool-call relevance, while SkCC studies
cross-framework functional portability. SkillDiff positions itself on a
different question: whether the same fixed skill/task/contract/workspace/
prompt/variant/repeat invariant preserves security conformance when only the
runtime profile changes.

MCP security work is similarly complementary. MCPShield, remote MCP
authentication measurement, the official MCP specification, MCP security best
practices, and OWASP MCP guidance focus on protocol, authorization,
server/client trust, tool invocation, and practitioner risk taxonomies.
SkillDiff uses MCP/tool behavior as one runtime dimension, but current evidence
is limited to bounded local fixtures and controlled traces. It is therefore a
differential runtime conformance methodology for portable skills, not another
skill scanner, harmful-skill corpus, least-privilege compiler, or MCP-only
defense.

## Submission Refresh Checklist

- Recheck all arXiv pages for revised versions.
- Recheck official MCP specification and security guidance for newer protocol
  versions.
- Recheck OWASP MCP Top 10 and OWASP Agentic Skills Top 10 project status.
- Keep external paper counts, rates, and performance numbers out of the main
  paper unless they are source-checked and cited at submission time.
- Keep SkillDiff result numbers in `paper/claim-ledger.json`; do not mix
  external related-work numerics with internal evidence claims.
