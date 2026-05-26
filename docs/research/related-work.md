# Related Work and Differentiation

This note supports `RM-02` in `research-roadmap.md`. Its purpose is to make the paper's novelty defensible against nearby agent-skill, MCP, and software supply-chain security work.

## Core Position

Recent work has studied several adjacent layers:

- **Skill/package scanning:** whether skill packages contain vulnerabilities, malicious instructions, or harmful capabilities.
- **Injected-skill benchmarks:** whether agents follow malicious skill-file instructions.
- **Task-conditioned least privilege:** whether a skill action exceeds what the user task requires.
- **Registry discovery and governance:** whether `SKILL.md` metadata manipulates discovery, selection, or admission.
- **Skill routing and pre-execution selection:** whether routers, internal
  selection signals, or detector layers select the right skill before any
  runtime action executes.
- **Cross-framework skill compilation:** whether skills can be transformed across framework formats.
- **MCP/tool security:** whether tools, descriptors, authorization, sampling, or cross-server flows are safe.
- **Runtime guardrails for tool-using agents:** whether tool calls align with the user's task under indirect prompt injection.

What remains under-characterized is the **portability boundary**: when the skill, task, and security contract are held fixed, do different runtimes preserve comparable security semantics in their observed file, shell, network, tool, approval, persistence, and data-flow behavior?

Differentiation sentence:

> Unlike prior work that scans skills, labels malicious skills, constrains over-privileged actions, attacks registry selection, compiles skills across frameworks, or hardens MCP protocols, this work treats the agent runtime itself as the security variable and measures cross-runtime behavioral drift under identical skill, task, contract, and adversarial conditions.

## Closest Agent-Skill Security Work

| Work | Problem | Method / Artifact | Dataset / Evaluation | Security Angle | What It Does Not Cover | Differentiation |
| --- | --- | --- | --- | --- | --- | --- |
| [Agent Skills in the Wild](https://arxiv.org/abs/2601.10338) | Ecosystem-wide skill vulnerability prevalence was unknown. | SkillScan, a multi-stage detector combining static analysis and LLM-based semantic classification. | 42,447 skills collected; 31,132 analyzed; 8,126 vulnerable skills used for taxonomy; reports 86.7% precision and 82.5% recall. | Prompt injection, data exfiltration, privilege escalation, supply-chain risk. | Cross-runtime behavior; runtime enforcement differences; whether the same skill behaves differently under different hosts. | This paper can reuse its vulnerability classes as seeds, but the measurement target is different: runtime traces and drift, not static vulnerability labels. |
| [Malicious Agent Skills in the Wild](https://arxiv.org/abs/2602.06547) | No ground-truth dataset existed for confirmed malicious agent skills. | Behavioral verification pipeline and malicious-skill labeling. | 98,380 skills inspected; 157 malicious skills confirmed; 632 vulnerabilities; reports data-thief and agent-hijacker archetypes. | Malicious skill threat characterization and ecosystem cleanup. | Cross-runtime containment, prompting, sandboxing, or differential execution behavior. | This paper is complementary: malicious skills can become adversarial probes, but the contribution is runtime conformance testing rather than a malicious-skill corpus. |
| [Skill-Inject](https://arxiv.org/abs/2602.20156) | Skill files can become prompt-injection supply-chain objects. | SkillInject benchmark for skill-file injection attacks. | 202 injection-task pairs; reports up to 80% attack success with frontier models. | Malicious or compromised skill-file instructions causing harmful behavior. | Benign skill drift; host/runtime differences when the skill is unchanged. | Skill-Inject asks whether agents follow malicious skill instructions. This paper asks whether identical skills produce different security outcomes because the runtime changes. |
| [SkillScope](https://arxiv.org/abs/2605.05868) | A skill can perform actions beyond the minimum necessary scope for the current task. | Graph-based instruction/code action modeling, replay validation, control-flow privilege constraining. | Reports 94.53% F1; validates 7,039 over-privileged skills; reduces triggered over-privileged action-in-task instances by 88.56%. | Task-conditioned least-privilege enforcement. | Runtime-to-runtime disagreement; comparing whether hosts allow, block, prompt, trace, or sandbox the same action. | SkillScope determines whether candidate actions are over-privileged for a task and constrains those actions within a skill execution model. This paper instead treats the runtime profile as the independent variable: filesystem scope, shell mediation, approval policy, network defaults, MCP/tool exposure, persistence, and tracing. SkillScope-style policies are a natural baseline or mitigation, but they do not measure whether two hosts enforce comparable security semantics for the same skill-task-contract triple. |
| [Under the Hood of SKILL.md](https://arxiv.org/abs/2605.11418) | `SKILL.md` text can manipulate skill discovery, selection, and governance. | SKILL.md-only attacks across Discovery, Selection, and Governance. | Real ClawHub skills; reports up to 86% pairwise win rate and 80% Top-10 placement in discovery, 77.6% adversarial selection rate, and 36.5%-100% governance evasion. | Semantic supply-chain attacks before runtime execution. | Post-selection runtime behavior and enforcement drift. | This paper starts after that attack path succeeds: once a skill is selected or installed, do runtime execution semantics contain or amplify the risk? |
| [SkCC](https://arxiv.org/abs/2605.03353) | Skills are hard to port because framework prompt formatting changes behavior. | Compiler with strongly typed SkIR, static optimizer, and framework emitters. | SkillsBench experiments; pass rate gains from 21.1% to 33.3% on Claude Code and 35.1% to 48.7% on Kimi CLI; reports sub-10ms compilation and 94.8% proactive security trigger rate. | Compile-time portability and static security hardening. | Runtime policy drift after deployment. | SkCC normalizes skills before execution. This paper tests whether normalized or identical skills still produce different security outcomes once executed by real runtimes. |
| [Agent Skills for Large Language Models](https://arxiv.org/abs/2602.12430) | The agent-skills field lacks a unified architecture and research map. | Survey and governance framework. | Survey; no new runtime dataset. | Architecture, acquisition, deployment, security, governance, and open challenges. | Experimental runtime drift benchmark. | This paper operationalizes one open challenge from the survey by turning skill portability into measurable security conformance tests. |

## Additional Close Work To Track

These works should be cited in a full paper to avoid looking selective. They are not the central competitors, but they shape the benchmark and mitigation baselines.

| Work | Layer | Relevance | Boundary |
| --- | --- | --- | --- |
| [HarmfulSkillBench](https://arxiv.org/abs/2604.15415) | Harmful-skill measurement and safety benchmark | Measures harmful skills across large registries and evaluates how pre-installed skills can lower refusal rates. | Studies harmful skill capabilities and model safety outcomes, not cross-runtime security conformance for a fixed skill-task-contract triple. |
| [BadSkill](https://arxiv.org/abs/2604.09378) | Model-in-skill supply-chain attack | Shows model-bearing skills can hide backdoors in bundled learned artifacts. | Focuses on poisoned skill internals; runtime drift can occur even when skill artifacts are fixed and non-poisoned. |
| [SkillRouter](https://arxiv.org/abs/2603.22455) | Skill selection and routing | Studies routing and selection of skills at scale. | Useful for activation and selection surfaces, but not a runtime conformance test after a fixed skill-task-contract triple has been selected. |
| [RouteGuard](https://arxiv.org/abs/2604.22888) | Pre-execution skill-poison detection | Uses internal selection signals to detect poisoned skill routing before execution. | A detector baseline for selection poisoning; SkillDiff measures post-selection runtime behavior under fixed inputs. |
| [ClawGuard](https://arxiv.org/abs/2604.11790) | Runtime tool-call boundary defense | Enforces user-confirmed rules at tool-call boundaries across web, local, MCP, and skill channels. | A strong mitigation baseline; this paper measures whether runtimes differ before and after such guardrails are applied. |
| [Task Shield](https://arxiv.org/abs/2412.16682) | Task-alignment defense for indirect prompt injection | Verifies whether instructions and tool calls contribute to user-specified goals. | Related to authorization and alignment of actions, but not a differential portability benchmark for skills. |
| [Agent Security Bench](https://arxiv.org/abs/2410.02644), [InjecAgent](https://arxiv.org/abs/2403.02691), and [AgentDojo](https://agentdojo.spylab.ai/) | Agent attack and indirect prompt-injection benchmarks | Provide benchmark design patterns for tool-using agents under adversarial external content. | They focus on broader attack success and defenses, not whether identical skills have stable security behavior across host runtimes. |

## Why Static Scanning Is Not Enough

Static skill scanning is necessary but incomplete because it treats the skill package as the main security object. Runtime-induced drift appears only when a skill is loaded and executed under a specific host policy. The same `SKILL.md` and helper script can be harmless when the runtime exposes only uploaded files, risky when it inherits a full workspace and shell, and partially contained when it runs in a network-disabled container with broad write access. A static scanner may flag suspicious code or text, but it cannot by itself determine whether a host will expose `.env`, require approval before network egress, trace tool calls, restrict writes, or silently persist state.

## Why Least Privilege Is a Mitigation, Not the Measurement Problem

Least privilege addresses one part of the risk: whether a skill receives more authority than a specific task requires. Runtime-induced drift is broader. It includes activation drift, approval drift, side-effect drift, data-flow drift, traceability differences, and inconsistent host behavior around the same declared capability. A least-privilege system can be evaluated as a mitigation inside this work, but the primary measurement question is whether existing runtimes preserve comparable security semantics when the skill and task are held constant.

## Why Cross-Framework Compilation Is Not Security Conformance

Skill compilers and intermediate representations can improve portability by translating skill structure across framework formats. That does not prove security behavior is preserved after deployment. A compiled skill may still be executed by runtimes with different filesystem roots, shell mediation, MCP clients, approval prompts, network defaults, persistent state, and logging behavior. This paper treats compilation as upstream of the problem: even if two hosts receive semantically equivalent skill artifacts, their realized security outcomes may diverge.

## MCP and Tool-Security Work

| Source | Security Layer | Core Contribution | Relevance | Distinction From Runtime-Induced Drift |
| --- | --- | --- | --- | --- |
| [Breaking the Protocol](https://arxiv.org/abs/2601.17549) | Protocol / architecture | Identifies capability-attestation gaps, bidirectional sampling without origin authentication, and implicit trust propagation; reports MCP increased attack success by 23-41% over comparable non-MCP setups and proposes MCPSec. | Relevant when skills depend on MCP tool access across hosts and servers. | Focuses on protocol design flaws and cross-server trust. Runtime drift can occur even with honest tools and unchanged protocol behavior. |
| [Securing the Model Context Protocol](https://arxiv.org/abs/2512.06556) | Tool metadata / semantic attack surface | Studies tool poisoning, shadowing, and rug pulls; proposes manifest signing, LLM-on-LLM vetting, and runtime guardrails. | Skills often depend on third-party descriptors and evolving tool registries. | The attacker changes tool metadata or descriptors. Runtime drift arises from different hosts interpreting the same skill contract and approval boundary differently. |
| [MCP Threat Modeling and Tool Poisoning](https://arxiv.org/abs/2603.22489) | MCP client implementation | Uses STRIDE and DREAD across MCP components; identifies tool poisoning as a major client-side risk; evaluates major clients. | Shows exploitability depends on client behavior, UI, validation, and sandboxing. | Centers malicious tool descriptions. Runtime drift asks what changes when the skill and tool are unchanged but the runtime differs. |
| [Official MCP specification and docs](https://modelcontextprotocol.io/specification/2025-11-25/basic) | Protocol semantics / host boundary | Defines resources, prompts, tools, transports, authorization, roots, and related capabilities. | Establishes that important safety behavior sits in client/host policy, approval UX, sandboxing, roots, and broker implementation. | The spec helps motivate drift: because many security choices are host-defined, portable skills can realize different security semantics under different MCP clients or hosts. |

Differentiation:

MCP work is closest when skills invoke tools through MCP-connected hosts. That literature studies protocol and descriptor trust: poisoned tool metadata, shadowing, rug pulls, sampling/authentication gaps, client validation, and cross-server trust propagation. This project uses those results to define MCP-connected runtime profiles and adversarial stressors.

The measurement variable here is different: with the skill, task, contract, and tool descriptors controlled, we ask whether host policy choices around roots, approvals, sandboxing, tool visibility, tracing, and data-flow brokerage lead to different contract outcomes.

## Drift Is Not Automatically A Failure

The paper should report two related but distinct outcomes:

- **Contract violation:** a denied event realizes outside the task-conditioned security contract by executing, exposing, persisting, transmitting, or completing. This is a security failure.
- **Attempted overreach:** a denied action is attempted but blocked, denied, or fails before exposure or side effect. This is a skill-behavior signal, not a realized security failure.
- **Runtime-pair disagreement:** two runtime profiles produce different security-relevant traces for the same skill-task-contract triple. This is a conformance signal that requires interpretation. Some disagreements are intended, such as a stricter runtime blocking a risky action that a permissive runtime allows.

This distinction prevents the paper from implying that every behavioral difference is a vulnerability.

## Methodological Prior Art

The method should be framed as differential security testing and conformance testing, not only as another agent benchmark with canaries. The core design follows a familiar security-testing pattern: hold the input artifact and task fixed, vary the implementation or policy boundary, record traces, and compare observed behavior against a specification. Here the implementation under test is the agent runtime profile, the specification is a task-conditioned security contract, and the evidence is a file/process/network/tool/approval/persistence/canary trace. This framing makes the paper legible to systems and security reviewers even if they are not already invested in agent-skill ecosystems.

## Software Supply-Chain Analogies

These ecosystems are useful as precedents, but they should be used as analogies rather than direct equivalences.

| Ecosystem | Useful Analogy | Boundary |
| --- | --- | --- |
| Browser extensions | Manifest-driven activation, permissioned execution, page/context-dependent behavior. | Does not model agent-style natural-language instruction following or task-conditioned runtime contracts. |
| npm / PyPI packages | Distribution, dependency risk, install-time trust, transitive behavior, environment-sensitive execution. | Does not capture host approval gates, tool mediation, or activation through semantic task matching. |
| VS Code extensions | Workspace-resident host extensions with activation events, editor state, file access, command APIs, and workspace trust. | Extension host policy is not the same as agent runtime policy or LLM-mediated tool use. |
| GitHub Actions | Workflow triggers, runner environment, token scopes, secrets, event-dependent execution. | CI workflows are explicit programs, not natural-language skills selected and interpreted by an agent. |
| CI/CD pipelines | Staged execution, isolated runners, provenance, approvals, environment-specific secrets. | Pipeline hardening alone does not solve agent runtime drift or user-task-conditioned behavior. |
| Plugin ecosystems | Host-mediated capability extension through declared APIs, metadata, and activation rules. | Most plugin systems do not combine natural-language instructions, executable tools, model context, and runtime approval semantics. |

Cross-cutting takeaway:

Across these ecosystems, a portable artifact does not fully determine behavior. The host runtime contributes permissions, context, activation rules, and policy, which can change the artifact's effective authority. Portable agent skills are distinct because they combine instruction text, activation metadata, executable components, runtime approvals, tool access, and context inheritance. The security question is therefore not only whether the package is trusted, but whether its behavior remains stable across runtimes.

## Terms To Use Carefully

| Term | Use In This Paper | Risk |
| --- | --- | --- |
| Runtime-induced drift | Primary phenomenon: security-relevant divergence caused by runtime policy differences. | Must define clearly so it does not sound like embedding or meaning drift. |
| Semantic drift | Avoid as primary term. Use only when discussing adjacent semantic manipulation work. | Can be confused with semantic supply-chain attacks or model meaning drift. |
| Least privilege | Treat as related mitigation and measurement dimension. | Do not let reviewers classify the paper as a SkillScope variant. |
| Skill portability | Use as the broad systems problem. | Clarify that the paper studies security portability, not only functional portability. |
| Security conformance | Use for the paper's high-level framing. | Must be backed by concrete contracts, traces, and drift metrics. |

## Related-Work Paragraph Draft

Recent work establishes that agent skills are a real security surface, but leaves open whether security behavior is preserved across runtimes. Large-scale studies such as Agent Skills in the Wild and Malicious Agent Skills in the Wild measure vulnerable and malicious skill prevalence, while Skill-Inject demonstrates that skill files can be used as prompt-injection supply-chain artifacts. SkillScope moves from static vulnerability labels toward task-conditioned least-privilege enforcement. Under the Hood of SKILL.md shows that skill metadata and instructions can manipulate discovery, selection, and governance, and SkCC addresses functional portability through a typed intermediate representation and framework-specific compilation. These works study skill content, registry behavior, task-conditioned over-privilege, or compile-time transformation. In contrast, this paper holds the skill-task pair constant and treats the runtime as the experimental variable, measuring whether activation, privilege, approval, side effects, and data flows remain stable across host environments.

MCP security work is similarly complementary. Protocol and tool-poisoning studies show that descriptors, sampling, authorization, trust propagation, and client validation can compromise tool-integrated agents. This paper uses those findings to motivate one class of runtime profiles, but asks a different question: even absent malicious tool metadata, do host policies around tools, roots, approvals, sandboxing, and data-flow brokerage produce different security outcomes for the same portable skill? The resulting contribution is a differential conformance methodology for skill runtimes, not another scanner, malicious-skill dataset, least-privilege compiler, or MCP-only threat model.
