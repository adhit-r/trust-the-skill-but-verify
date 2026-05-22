# Privacy Guardrails for Enterprise Compliance Data

This document defines the data privacy architecture for the auditlens skill. Compliance evidence is among the most sensitive data an organization possesses — policies, access controls, vulnerability reports, vendor contracts, personnel records. These guardrails ensure this data is handled with the protection it demands.

## Table of Contents
1. [The Privacy Problem](#problem)
2. [Anthropic's Data Tiers — What Actually Protects You](#tiers)
3. [Deployment Recommendations by Risk Level](#deployment)
4. [Technical Guardrails Built Into This Skill](#technical)
5. [Data Handling Rules for the Skill](#rules)
6. [Privacy Checklist for Enterprise Users](#checklist)
7. [Compliance-Specific Sensitivity Classes](#classes)

---

## 1. The Privacy Problem {#problem}

When you feed compliance evidence into Claude, you're sharing:
- Security policies revealing your defensive architecture
- Vulnerability scan reports showing your weaknesses
- Access control matrices showing who has access to what
- Vendor contracts with pricing and SLA terms
- Incident response playbooks detailing your response capabilities
- Personnel records (background checks, training completions)
- Risk registers quantifying your threat landscape

This is exactly the kind of data that should NEVER end up in model training. A competitor or attacker learning your security posture from an AI model's training data is a nightmare scenario.

---

## 2. Anthropic's Data Tiers — What Actually Protects You {#tiers}

### Tier 1: SAFE — Commercial Terms (No Training)

| Product | Training? | Retention | Notes |
|---------|----------|-----------|-------|
| Claude for Work (Team) | NO | 30 days default | Commercial Terms apply |
| Claude for Work (Enterprise) | NO | Configurable, ZDR available | Strongest protections |
| Anthropic API | NO | 30 days default | Commercial Terms |
| Amazon Bedrock (Claude) | NO | Per AWS agreement | AWS data controls apply |
| Google Vertex AI (Claude) | NO | Per GCP agreement | GCP data controls apply |
| Claude Gov | NO | Per gov agreement | FedRAMP controls |
| Claude for Education | NO | Per edu agreement | FERPA aligned |

Under Commercial Terms, Anthropic explicitly does not train generative models on your inputs or outputs.

Enterprise tier also offers Zero Data Retention (ZDR) — inputs and outputs are not stored at all beyond abuse screening.

### Tier 2: CONDITIONAL — Consumer Plans (Opt-Out Required)

| Product | Training Default | Can Opt Out? | Retention (Training ON) | Retention (Training OFF) |
|---------|-----------------|-------------|------------------------|-------------------------|
| Claude Free | ON | Yes | 5 years | 30 days |
| Claude Pro | ON | Yes | 5 years | 30 days |
| Claude Max | ON | Yes | 5 years | 30 days |
| Claude Code (consumer accts) | ON | Yes | 5 years | 30 days |

CRITICAL: If using consumer plans for compliance work:
1. Go to Settings > Privacy > Privacy Settings
2. Turn OFF "Help improve Claude" / model training toggle
3. This must be done BEFORE uploading any sensitive documents
4. Use Incognito chats — these are NEVER used for training regardless of settings

### Tier 3: ADDITIONAL PROTECTIONS — Platform-Level

| Protection | How to Enable |
|-----------|--------------|
| Zero Data Retention (ZDR) | Enterprise API only, request from account team |
| VPN/Proxy compatibility | Claude Code supports most VPNs |
| SSO/SCIM | Enterprise plan |
| Audit logs | Enterprise plan |
| Data residency | Available on select plans |

---

## 3. Deployment Recommendations by Risk Level {#deployment}

### For Highly Sensitive Compliance Work (Recommended)

Use one of these architectures, ranked from most to least protective:

**Architecture A: Self-Hosted / Air-Gapped (Maximum Security)**
- Run a local LLM (Llama, Mistral) for the most sensitive analysis
- Use Claude API with ZDR only for non-sensitive orchestration
- Evidence never leaves your infrastructure

**Architecture B: Enterprise API with ZDR**
- Claude for Work Enterprise with Zero Data Retention enabled
- Data processed but not stored by Anthropic
- Suitable for most enterprise compliance workflows

**Architecture C: Commercial API (Standard)**
- Anthropic API under Commercial Terms
- No training on your data, 30-day retention
- Good balance of capability and protection

**Architecture D: Consumer with Safeguards (Minimum Viable)**
- Claude Pro/Max with training explicitly OFF
- Use Incognito mode for all compliance sessions
- Delete conversations after extracting outputs
- NOT recommended for highly sensitive data

### Decision Matrix

| Data Sensitivity | Recommended Architecture | Minimum Architecture |
|-----------------|------------------------|---------------------|
| Top Secret / Classified | A (Air-Gapped) | A only |
| Highly Confidential (PII, PHI, financial) | B (Enterprise ZDR) | C (Commercial API) |
| Confidential (policies, procedures) | C (Commercial API) | D (Consumer + safeguards) |
| Internal (general documentation) | C or D | D |

---

## 4. Technical Guardrails Built Into This Skill {#technical}

### 4a. Pre-Flight Privacy Check

At the START of every compliance audit session, the skill MUST run this check and display the results:

```
╔══════════════════════════════════════════════╗
║         PRIVACY GUARDRAIL CHECK              ║
╠══════════════════════════════════════════════╣
║ Platform:     [Claude.ai / API / Enterprise] ║
║ Plan tier:    [Free/Pro/Max/Team/Enterprise]  ║
║ Training:     [ON ⚠️ / OFF ✅]               ║
║ Incognito:    [Yes ✅ / No ⚠️]               ║
║ ZDR:          [Enabled / Not available]      ║
╠══════════════════════════════════════════════╣
║ RECOMMENDATION: [Safe to proceed / Warning]  ║
╚══════════════════════════════════════════════╝
```

If the check detects consumer plan with training ON:
- Display a WARNING before processing any files
- Recommend switching to Incognito or disabling training
- Ask for explicit confirmation before proceeding
- Suggest upgrading to a commercial plan for ongoing use

### 4b. Data Minimization

The skill should extract and process only what's needed:

- **Summaries over full text**: Classify documents by reading summaries and key sections, not ingesting entire 100-page policies verbatim
- **Metadata over content**: Use file metadata (names, dates, sizes, authors) for cataloging when possible
- **Local processing first**: Run the Python classification script locally rather than sending all content through the API
- **Structured outputs only**: Evidence catalogs, gap reports, and provenance chains are structured JSON — the raw document content should not persist in conversation history

### 4c. PII/PHI Detection and Redaction

Before processing documents, scan for and flag:
- Email addresses → redact to `[EMAIL]`
- Phone numbers → redact to `[PHONE]`
- SSN/Tax IDs → redact to `[SSN]`
- Credit card numbers → redact to `[CC]`
- Names in HR documents → redact to `[NAME]` unless needed for ownership tracking
- IP addresses in security logs → redact to `[IP]`
- Specific vulnerability details (CVE + affected system + version) → generalize

### 4d. Output Sanitization

All outputs (HTML reports, JSON exports, CSV trackers) should:
- Not contain raw document text beyond necessary excerpts
- Redact PII/PHI in any exported reports
- Include a data classification header: "CONFIDENTIAL — [Organization Name] — Compliance Assessment"
- Include a retention notice: "This report contains sensitive security information. Handle per your organization's data classification policy."

### 4e. Conversation Hygiene

After completing a compliance audit session:
- Remind the user to delete the conversation if on a consumer plan
- All working files should be in `/home/claude/` (ephemeral, wiped between sessions)
- Final outputs go to `/mnt/user-data/outputs/` for download, then the user should delete the chat
- Never suggest resuming a compliance audit conversation — start fresh each time

---

## 5. Data Handling Rules for the Skill {#rules}

These rules MUST be followed by the skill during execution:

1. **Never echo back full document content** — Summarize, classify, and reference, but don't reproduce entire policy texts in responses
2. **Never store credentials** — If gws/m365 CLI auth is discussed, never log tokens or secrets
3. **Never include raw vulnerability data in HTML exports** — Gap reports should describe control deficiencies, not specific CVEs + affected systems
4. **Always classify before processing** — Run the pre-flight privacy check before ingesting any documents
5. **Prefer local script execution** — Use `classify_evidence.py` and other scripts locally rather than sending all document text through the conversation
6. **Minimize conversation context** — Use structured JSON intermediate representations, not raw text dumps
7. **Warn on external sharing** — If the user asks to share audit results externally, remind them to review for sensitive content first
8. **Respect data residency** — If the user mentions EU/GDPR requirements, note that Anthropic's data processing may involve US-based infrastructure (unless using a region-specific deployment)

---

## 6. Privacy Checklist for Enterprise Users {#checklist}

Before starting a compliance audit with this skill, verify:

- [ ] **Plan check**: Confirm you're on a commercial plan (Team, Enterprise, API) — or have training OFF + Incognito if consumer
- [ ] **Training toggle**: Verify "Help improve Claude" is OFF in Settings > Privacy
- [ ] **Incognito mode**: Enable for this session if on a consumer plan
- [ ] **Data classification**: Confirm the sensitivity level of documents you'll upload
- [ ] **Scope agreement**: Define what documents will be analyzed (don't upload more than needed)
- [ ] **Output handling**: Plan where audit outputs will be stored after download
- [ ] **Cleanup plan**: Decide when to delete this conversation after extracting results
- [ ] **Team awareness**: Ensure anyone with access to this chat understands the sensitivity

---

## 7. Compliance-Specific Sensitivity Classes {#classes}

Not all compliance evidence is equally sensitive. The skill should apply proportional protections:

| Class | Examples | Handling |
|-------|----------|---------|
| **CRITICAL** | Pen test reports, vulnerability scans, incident details, cryptographic key policies | Process only via Enterprise ZDR or local scripts. Never echo raw content. |
| **HIGH** | Access control matrices, network diagrams, vendor security assessments, risk registers | Commercial API minimum. Summarize, don't reproduce. |
| **MEDIUM** | Policies, procedures, standards, training records, BCP plans | Commercial API recommended. Can reference sections. |
| **LOW** | Published policies, compliance certificates, public attestation reports | Standard handling acceptable. |

The pre-flight check should ask the user what sensitivity class their documents fall into and adjust behavior accordingly.
