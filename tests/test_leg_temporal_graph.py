"""Tests for Module 2 (LEG-1): Point-in-Time Legal Knowledge Graph & Old-vs-New Diff Builder."""
from __future__ import annotations

from datetime import date
from pathlib import Path

from scripts.generate_synthetic_corp_data import build_scenario_s_leg
from src.leg_timeline_auditor.temporal_law_graph import TemporalLegalGraph


def test_scenario_s_leg_accurately_separates_effective_vs_upcoming_rules() -> None:
    root = Path(__file__).resolve().parent.parent
    report = build_scenario_s_leg(root / "rules" / "kr_corporate_law_2025_2027.yaml")

    # As of 2026-10-25:
    # 1) LAW-2026-02 (2026-08-20 short-term parental leave) -> Layer A mandatory block
    # 2) LAW-2026-03 (2026-09-18 spouse miscarriage leave & 50-day prior usage) -> Layer A mandatory block
    # 3) LAW-2026-05 (2026-11-27 subfertility leave 4 days paid) -> Layer B upcoming advisory
    assert report.can_issue_compliance_certificate is False
    assert report.layer_a_mandatory_count == 2
    assert report.layer_b_upcoming_count == 1

    layer_a_ids = [item.rule_id for item in report.diff_table if item.layer == "A"]
    layer_b_ids = [item.rule_id for item in report.diff_table if item.layer == "B"]
    assert layer_a_ids == ["LAW-2026-02", "LAW-2026-03"]
    assert layer_b_ids == ["LAW-2026-05"]


def test_temporal_partition_shifts_when_audit_date_advances_to_2026_12_01() -> None:
    root = Path(__file__).resolve().parent.parent
    graph = TemporalLegalGraph.from_yaml(root / "rules" / "kr_corporate_law_2025_2027.yaml")
    part_oct = graph.partition_by_audit_date(date(2026, 10, 25))
    part_dec = graph.partition_by_audit_date(date(2026, 12, 1))

    # LAW-2026-05 (2026-11-27) moves from upcoming in Oct to effective in Dec
    assert any(n.rule_id == "LAW-2026-05" for n in part_oct["upcoming"])
    assert any(n.rule_id == "LAW-2026-05" for n in part_dec["effective"])
