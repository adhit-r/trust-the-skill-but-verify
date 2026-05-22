# Open Security Architecture (OSA) — Compliance Mapping Connector

> **Data Source**: [opensecurityarchitecture.org](https://www.opensecurityarchitecture.org)
> **License**: CC BY-SA 4.0 — Attribution required in all outputs using this data
> **GitHub**: [opensecurityarchitecture/osa-data](https://github.com/opensecurityarchitecture/osa-data)

## What OSA Provides

315 NIST 800-53 Rev 5 controls, each mapped to **87 compliance frameworks**. NIST 800-53 acts as the universal parent — satisfy one control, automatically identify coverage across every mapped framework.

## How to Use

### 1. API Access (Preferred when network is available)

```
GET https://www.opensecurityarchitecture.org/api/controls/{control-id}
```

Example: `GET /api/controls/AC-01`

Returns a JSON object with:
- `id`, `name`, `family`, `description`
- `compliance_mappings` — object with 87 framework keys, each containing an array of mapped control IDs
- `attack_techniques` — MITRE ATT&CK technique IDs this control mitigates

**OpenAPI spec**: `https://www.opensecurityarchitecture.org/openapi.yaml`

### 2. GitHub Raw Data (Fallback)

```
https://raw.githubusercontent.com/opensecurityarchitecture/osa-data/main/data/controls/{CONTROL-ID}.json
```

Note: Control IDs in filenames are uppercase (e.g., `AC-01.json`, not `ac-01.json`).

### 3. Full Catalog

```
https://raw.githubusercontent.com/opensecurityarchitecture/osa-data/main/data/controls/_catalog.json
```

## The compliance_mappings Schema

Each control's `compliance_mappings` object uses these keys:

| Key | Framework | Region |
|-----|-----------|--------|
| `iso_27001_2022` | ISO 27001:2022 | International |
| `iso_27002_2022` | ISO 27002:2022 | International |
| `iso_42001_2023` | ISO/IEC 42001:2023 (AI Management) | International |
| `soc2_tsc` | SOC 2 Trust Service Criteria | US |
| `pci_dss_v4` | PCI DSS v4.0.1 | International |
| `cobit_2019` | COBIT 2019 | International |
| `cis_controls_v8` | CIS Controls v8 | International |
| `nist_csf_2` | NIST CSF 2.0 | US |
| `csa_ccm_v4` | CSA Cloud Controls Matrix v4 | International |
| `csa_aicm` | CSA AI Controls Matrix v1 | International |
| `gdpr` | EU GDPR | EU |
| `dora` | EU DORA | EU |
| `nis2` | NIS2 Directive | EU |
| `cra` | EU Cyber Resilience Act | EU |
| `mica` | MiCA (Markets in Crypto-Assets) | EU |
| `solvency_ii` | Solvency II | EU |
| `hipaa_sr` | HIPAA Security Rule | US |
| `nydfs_500` | NYDFS Cybersecurity Regulation | US |
| `ffiec_is` | FFIEC Information Security | US |
| `cmmc_2` | CMMC 2.0 | US |
| `nerc_cip` | NERC CIP | US |
| `fda_21_cfr_11` | FDA 21 CFR Part 11 | US |
| `fda_cyber` | FDA Cybersecurity Guidance | US |
| `hitrust_csf` | HITRUST CSF v11 | US |
| `anssi` | ANSSI (France) | France |
| `bsi_grundschutz` | BSI IT-Grundschutz | Germany |
| `finma_circular` | FINMA Circular 2023/1 | Switzerland |
| `osfi_b13` | OSFI B-13 | Canada |
| `mas_trm` | MAS TRM | Singapore |
| `hkma_tme1` | HKMA TM-E-1 | Hong Kong |
| `rbi_csf` | RBI Cyber Security Framework | India |
| `fisc` | FISC Security Guidelines | Japan |
| `mlps_2` | MLPS 2.0 | China |
| `sama_csf` | SAMA Cyber Security Framework | Saudi Arabia |
| `nca_ecc` | NCA ECC | Saudi Arabia |
| `uae_ia` | UAE Information Assurance | UAE |
| `cbb_tm` | CBB Technology Management | Bahrain |
| `qatar_nia` | Qatar NIA | Qatar |
| `cbuae` | CBUAE | UAE |
| `cbe_csf` | CBE Cyber Security Framework | Egypt |
| `cbn_csf` | CBN Cyber Security Framework | Nigeria |
| `bog_cisd` | BoG CISD | Ghana |
| `popia` | POPIA | South Africa |
| `sa_js2` | SA JS2 | South Africa |
| `bom_ctrm` | BoM CTRM | Mauritius |
| `lgpd_bcb` | LGPD + BCB 4893 | Brazil |
| `bot_cyber` | BOT Cyber Resilience | Thailand |
| `sebi_cscrf` | SEBI CSCRF | India |
| `bio2` | BIO2 | Netherlands |
| `dnb_good_practice` | DNB Good Practice | Netherlands |
| `eba_ict` | EBA ICT Guidelines | EU |
| `ecb_croe` | ECB CROE | EU |
| `bcbs_239` | BCBS 239 | International |
| `cpmi_pfmi` | CPMI-IOSCO PFMI | International |
| `iosco_cyber` | IOSCO Cyber Resilience | International |
| `isae_3402` | ISAE 3402 | International |
| `common_criteria` | Common Criteria | International |
| `tiber_eu` | TIBER-EU | EU |
| `cbest` | CBEST | UK |
| `pci_hsm` | PCI HSM | International |
| `pci_pts` | PCI PTS v6 | International |
| `fips_140` | FIPS 140-3 | US |
| `pra_ss1_23` | PRA SS1/23 | UK |
| `pra_op_resilience` | PRA Operational Resilience | UK |
| `fca_sysc_13` | FCA SYSC 13 | UK |
| `lloyds_ms` | Lloyd's Minimum Standards | UK |
| `naic_ds` | NAIC Insurance Data Security | US |
| `nhs_dspt` | NHS DSPT | UK |
| `iso_27799` | ISO 27799 | International |
| `owasp_masvs_v2` | OWASP MASVS v2.1 | International |
| `ccss_v9` | CCSS v9.0 | International |
| `basel_sco60` | Basel SCO60 | International |
| `bssc` | BSSC Standards | International |
| `sec_custody_digital` | SEC Custody (Digital Assets) | US |
| `swift_cscf` | SWIFT CSCF | International |
| `iec_62443` | IEC 62443 | International |
| `asd_e8` | ASD Essential Eight | Australia |
| `apra_cps_234` | APRA CPS 234 | Australia |
| `finos_ccc` | FINOS CCC | International |
| `ferc_cip` | FERC CIP Orders | US |
| `doe_c2m2` | DOE C2M2 v2.1 | US |

## NIST 800-53 Control Families

| Family | ID | Controls |
|--------|-----|----------|
| Access Control | AC | 25 |
| Awareness and Training | AT | 6 |
| Audit and Accountability | AU | 16 |
| Security Assessment | CA | 9 |
| Configuration Management | CM | 14 |
| Contingency Planning | CP | 13 |
| Identification and Authentication | IA | 12 |
| Incident Response | IR | 9 |
| Maintenance | MA | 7 |
| Media Protection | MP | 8 |
| Physical and Environmental | PE | 23 |
| Planning | PL | 11 |
| Program Management | PM | 32 |
| Personnel Security | PS | 9 |
| PII Processing and Transparency | PT | 8 |
| Risk Assessment | RA | 10 |
| System and Services Acquisition | SA | 18 |
| System and Communications Protection | SC | 50 |
| System and Information Integrity | SI | 23 |
| Supply Chain Risk Management | SR | 12 |

## Agent Workflow: Reverse Mapping

When the user provides evidence mapped to ANY framework, use OSA to find the NIST 800-53 parent, then cascade:

```
User's Evidence → Framework Control (e.g., ISO 27001 A.5.1)
                → OSA lookup: which NIST 800-53 controls map to A.5.1?
                → Answer: AC-01
                → OSA lookup: what else maps to AC-01?
                → Answer: SOC 2 CC5.3, HIPAA §164.316(a), PCI DSS 12.1, GDPR Art.24(1), ...
                → Auto-mark all as "partially covered by same evidence"
```

### Framework Coverage Calculator

Given the user's current framework certifications, calculate coverage for target frameworks:

1. Collect all controls satisfied in the current framework
2. For each control, find the NIST 800-53 parent via OSA
3. For each NIST 800-53 control, check if it maps to the target framework
4. Calculate: `coverage = (mapped target controls / total target controls) × 100%`

Example output:
```
SOC 2 Type II → ISO 27001:2022 Coverage: 72%
  Covered: A.5.1, A.5.2, A.5.7, A.5.9, A.5.15, A.5.24, A.6.3, A.7.1, A.8.5, ...
  Gaps: A.5.23, A.5.29, A.7.3, A.7.4, A.8.1, A.8.8, A.8.13, ...
```

## Attribution Requirements

When using OSA data in any output, include:

```
Compliance mappings sourced from Open Security Architecture (opensecurityarchitecture.org)
Licensed under CC BY-SA 4.0
```
