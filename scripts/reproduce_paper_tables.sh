#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT"

PYTHON_BIN="${PYTHON_BIN:-python3}"
ARTIFACT_OUTPUT_ROOT="${ARTIFACT_OUTPUT_ROOT:-}"
export PYTHONDONTWRITEBYTECODE=1

artifact_path() {
  local rel_path="$1"
  if [[ -n "$ARTIFACT_OUTPUT_ROOT" ]]; then
    printf '%s\n' "$ARTIFACT_OUTPUT_ROOT/$rel_path"
  else
    printf '%s\n' "$ROOT/$rel_path"
  fi
}

run() {
  echo "==> $*"
  "$@"
}

if [[ -n "$ARTIFACT_OUTPUT_ROOT" ]]; then
  mkdir -p "$ARTIFACT_OUTPUT_ROOT"
fi

BENCHMARK_CASES="benchmark/manifests/benchmark-cases-current.json"
BENCHMARK_SCALE_GAP="$(artifact_path "results/derived/benchmark-scale-gap.json")"
PAIRED_RUNTIME_SUMMARY="$(artifact_path "results/derived/paired-runtime-summary.json")"
GATE5_INCLUSION_TABLE="$(artifact_path "benchmark/manifests/gate5-paper-inclusion.json")"
GATE5_DESCRIPTIVE_RATES="$(artifact_path "results/derived/gate5-descriptive-rates.json")"
GATE5_STATISTICAL_INTERVALS="$(artifact_path "results/derived/gate5-statistical-intervals.json")"
GATE5_REVIEW_QUEUE="$(artifact_path "benchmark/review/gate5-review-queue.json")"
GATE5_REVIEW_PACKET_INDEX="$(artifact_path "benchmark/review/gate5-review-packet-index.json")"
GATE5_BLINDED_PACKET_BUNDLE="$(artifact_path "benchmark/review/gate5-blinded-packet-bundle.json")"
GATE5_REVIEW_EXPORT_TEMPLATES="$(artifact_path "benchmark/review/gate5-review-export-templates.json")"
RUNTIME_REPORT_CARDS_DIR="$(artifact_path "results/derived/runtime-report-cards")"
RUNTIME_REPORT_CARD_TABLE="$(artifact_path "paper/tables/runtime-report-card-summary.md")"

run "$PYTHON_BIN" tools/validate_benchmark_cases.py --self-test "$BENCHMARK_CASES"

run "$PYTHON_BIN" tools/build_benchmark_scale_gap.py \
  --manifest "$BENCHMARK_CASES" \
  --output "$BENCHMARK_SCALE_GAP"
run "$PYTHON_BIN" tools/validate_benchmark_scale_gap.py --report "$BENCHMARK_SCALE_GAP"

run "$PYTHON_BIN" tools/build_paired_runtime_summary.py --output "$PAIRED_RUNTIME_SUMMARY"
run "$PYTHON_BIN" tools/validate_paired_runtime_summary.py --summary "$PAIRED_RUNTIME_SUMMARY"

run "$PYTHON_BIN" tools/build_gate5_inclusion_table.py \
  --manifest "$BENCHMARK_CASES" \
  --paired-summary "$PAIRED_RUNTIME_SUMMARY" \
  --output "$GATE5_INCLUSION_TABLE"
run "$PYTHON_BIN" tools/validate_gate5_inclusion_table.py --table "$GATE5_INCLUSION_TABLE"

run "$PYTHON_BIN" tools/build_gate5_descriptive_rates.py \
  --inclusion-table "$GATE5_INCLUSION_TABLE" \
  --paired-summary "$PAIRED_RUNTIME_SUMMARY" \
  --output "$GATE5_DESCRIPTIVE_RATES"
run "$PYTHON_BIN" tools/validate_gate5_descriptive_rates.py --report "$GATE5_DESCRIPTIVE_RATES"

run "$PYTHON_BIN" tools/build_gate5_statistical_intervals.py \
  --inclusion-table "$GATE5_INCLUSION_TABLE" \
  --descriptive-rates "$GATE5_DESCRIPTIVE_RATES" \
  --paired-summary "$PAIRED_RUNTIME_SUMMARY" \
  --output "$GATE5_STATISTICAL_INTERVALS"
run "$PYTHON_BIN" tools/validate_gate5_statistical_intervals.py --report "$GATE5_STATISTICAL_INTERVALS"

run "$PYTHON_BIN" tools/build_gate5_review_queue.py \
  --inclusion-table "$GATE5_INCLUSION_TABLE" \
  --paired-summary "$PAIRED_RUNTIME_SUMMARY" \
  --output "$GATE5_REVIEW_QUEUE"
run "$PYTHON_BIN" tools/validate_gate5_review_queue.py --queue "$GATE5_REVIEW_QUEUE"

run "$PYTHON_BIN" tools/build_gate5_review_packet_index.py \
  --queue "$GATE5_REVIEW_QUEUE" \
  --output "$GATE5_REVIEW_PACKET_INDEX"
run "$PYTHON_BIN" tools/validate_gate5_review_packet_index.py --index "$GATE5_REVIEW_PACKET_INDEX"

run "$PYTHON_BIN" tools/build_gate5_blinded_packet_bundle.py \
  --index "$GATE5_REVIEW_PACKET_INDEX" \
  --output "$GATE5_BLINDED_PACKET_BUNDLE"
run "$PYTHON_BIN" tools/validate_gate5_blinded_packet_bundle.py --bundle "$GATE5_BLINDED_PACKET_BUNDLE"

run "$PYTHON_BIN" tools/build_gate5_review_export_templates.py \
  --bundle "$GATE5_BLINDED_PACKET_BUNDLE" \
  --output "$GATE5_REVIEW_EXPORT_TEMPLATES"
run "$PYTHON_BIN" tools/validate_gate5_review_export_templates.py --package "$GATE5_REVIEW_EXPORT_TEMPLATES"

run "$PYTHON_BIN" tools/build_runtime_report_cards.py \
  --output-dir "$RUNTIME_REPORT_CARDS_DIR"
run "$PYTHON_BIN" tools/build_runtime_report_cards.py \
  --check \
  --output-dir "$RUNTIME_REPORT_CARDS_DIR"
run "$PYTHON_BIN" tools/build_runtime_report_card_table.py \
  --cards-dir "$RUNTIME_REPORT_CARDS_DIR" \
  --output "$RUNTIME_REPORT_CARD_TABLE"
run "$PYTHON_BIN" tools/build_runtime_report_card_table.py \
  --check \
  --cards-dir "$RUNTIME_REPORT_CARDS_DIR" \
  --output "$RUNTIME_REPORT_CARD_TABLE"

run "$PYTHON_BIN" tools/validate_source_mix_rp6_report_card.py
run "$PYTHON_BIN" tools/build_source_mix_rp6_repeat_stability.py --check
run "$PYTHON_BIN" tools/validate_repeat_coverage.py
run "$PYTHON_BIN" tools/validate_gate5_scaffolds.py
run "$PYTHON_BIN" tools/validate_paper_figures.py
run "$PYTHON_BIN" tools/validate_claim_ledger.py
run "$PYTHON_BIN" tools/check_no_local_paths.py

if [[ -n "$ARTIFACT_OUTPUT_ROOT" ]]; then
  echo "paper table artifacts rebuilt under $ARTIFACT_OUTPUT_ROOT"
else
  echo "paper table artifacts rebuilt in tracked paths"
fi
