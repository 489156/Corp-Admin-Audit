"""Automated Corporate Rulebook & Standard Contract Compliance Auditor and Old-vs-New Table Builder."""
from __future__ import annotations

from dataclasses import dataclass
from datetime import date
from typing import Dict, List

from src.leg_timeline_auditor.temporal_law_graph import LawAmendmentNode, TemporalLegalGraph


@dataclass(frozen=True)
class ClauseDiffItem:
    rule_id: str
    statute: str
    topic: str
    effective_date: str
    severity_badge: str        # "🟥 [A층 하드블록: 즉시개정 필수]" | "🟧 [B층 권고: 사전개정 준비]" | "🟢 [적법 반영]"
    layer: str                 # "A" | "B" | "PASS"
    current_rulebook_excerpt: str
    recommended_amendment: str
    missing_keywords: List[str]


@dataclass(frozen=True)
class RulebookAuditReport:
    audit_date: str
    can_issue_compliance_certificate: bool
    layer_a_mandatory_count: int
    layer_b_upcoming_count: int
    diff_table: List[ClauseDiffItem]


def audit_corporate_rulebook(
    rulebook_clauses: Dict[str, str],
    graph: TemporalLegalGraph,
    audit_date: date,
) -> RulebookAuditReport:
    """Compares corporate rulebook clauses by category against the Point-in-Time Legal Graph."""
    diff_items: List[ClauseDiffItem] = []
    a_count = 0
    b_count = 0

    for node in graph.nodes:
        current_text = rulebook_clauses.get(node.category, "").strip()
        missing_kw = [kw for kw in node.required_keywords if kw not in current_text]
        has_legacy_violation = any(pat in current_text for pat in node.legacy_violation_patterns)
        is_non_compliant = bool(missing_kw) or has_legacy_violation or not current_text

        if not is_non_compliant:
            diff_items.append(
                ClauseDiffItem(
                    rule_id=node.rule_id,
                    statute=node.statute,
                    topic=node.topic,
                    effective_date=node.effective_date.isoformat(),
                    severity_badge="🟢 [적법 반영]",
                    layer="PASS",
                    current_rulebook_excerpt=current_text,
                    recommended_amendment="현행 조문 적법 유지",
                    missing_keywords=[],
                )
            )
            continue

        if node.effective_date <= audit_date and node.is_mandatory:
            a_count += 1
            badge = "🟥 [A층 하드블록: 즉시개정 필수]"
            layer = "A"
        else:
            b_count += 1
            badge = "🟧 [B층 권고: 사전개정 준비]"
            layer = "B"

        diff_items.append(
            ClauseDiffItem(
                rule_id=node.rule_id,
                statute=node.statute,
                topic=node.topic,
                effective_date=node.effective_date.isoformat(),
                severity_badge=badge,
                layer=layer,
                current_rulebook_excerpt=current_text or "(사내규정 내 해당 조문 누락)",
                recommended_amendment=node.standard_clause_template,
                missing_keywords=missing_kw,
            )
        )

    return RulebookAuditReport(
        audit_date=audit_date.isoformat(),
        can_issue_compliance_certificate=(a_count == 0),
        layer_a_mandatory_count=a_count,
        layer_b_upcoming_count=b_count,
        diff_table=diff_items,
    )
