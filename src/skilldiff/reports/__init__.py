"""Report renderers for SkillDiff."""

from .contract_compare import write_comparison_report
from .runtime_report_card import runtime_report_card_texts, write_runtime_report_card

__all__ = ["runtime_report_card_texts", "write_comparison_report", "write_runtime_report_card"]
