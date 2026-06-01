# Gate 5 Human Review Handoff

Status: handoff package ready; no completed human review.

Date: 2026-06-01, Asia/Kolkata.

## Handoff Inputs

- Review queue: `benchmark/review/gate5-review-queue.json`
- Review packet index: `benchmark/review/gate5-review-packet-index.json`
- Blinded packet bundle: `benchmark/review/gate5-blinded-packet-bundle.json`
- Blank reviewer templates: `benchmark/review/gate5-review-export-templates.json`
- Reviewer A worksheet: `benchmark/review/gate5-reviewer-a-worksheet.csv`
- Reviewer A worksheet guide: `benchmark/review/gate5-reviewer-a-worksheet.md`
- Completed export schema: `schemas/gate5_completed_review_export.schema.json`
- Completed export validator: `tools/validate_gate5_completed_review_export.py`
- Worksheet builder: `tools/build_gate5_human_review_worksheet.py`
- Worksheet converter: `tools/convert_gate5_human_review_worksheet.py`
- Worksheet validator: `tools/validate_gate5_human_review_worksheet.py`
- Adjudication form: `paper/gate5-adjudication-form.md`

## Current Counts

- Queued items: `132`
- Blinding-eligible items: `122`
- Exported blinded packets: `122`
- Blocked metadata-only packets: `10`
- Reviewer templates: `2`
- Assigned pair-review units per template: `122`
- Completed review exports: `0`
- Human reviewer identities claimed: `0`
- Agreement metrics: `0`
- Adjudication records: `0`

## Reviewer Procedure

1. Assign two independent real human reviewers.
2. Copy one template per reviewer from
   `benchmark/review/gate5-review-export-templates.json`.
3. Reviewer A may use `benchmark/review/gate5-reviewer-a-worksheet.csv` as a
   spreadsheet-friendly blank worksheet generated from the frozen template.
4. Each reviewer fills every response field for all `122` assigned pair-review
   units without using Codex-assisted labels as human review evidence.
5. Convert a completed worksheet to the completed-review export format:

```sh
python3 tools/convert_gate5_human_review_worksheet.py \
  --worksheet benchmark/review/gate5-reviewer-a-worksheet.csv \
  --reviewer-slot reviewer_a \
  --reviewer-id human-REPLACE_ME \
  --review-timestamp-utc YYYY-MM-DDTHH:MM:SSZ \
  --output benchmark/review/completed/gate5-reviewer_a-completed-review.json
```

6. Validate each completed export:

```sh
python3 tools/validate_gate5_completed_review_export.py <completed-review-export.json>
```

7. Compute reviewer agreement and adjudication only after two validated exports
   cover the same frozen item set.

## Boundaries

- This handoff does not claim completed human review.
- This handoff does not claim reviewer agreement, Cohen's kappa, adjudication,
  completed statistics, McNemar tests, prevalence, or paper-grade completion.
- Codex-assisted, synthetic, anonymous, placeholder, fake, dummy, or test
  reviewer IDs do not count as human review evidence.

## Verification

Run:

```sh
python3 tools/validate_gate5_human_review_handoff.py
python3 tools/validate_gate5_human_review_worksheet.py
```

`make verify` runs this validator.
