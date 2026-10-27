"""Tests for Module 3 (IR-1): Ledger-Bound Fact Verification & Selective Disclosure Detector (SDI)."""
from __future__ import annotations

import pytest

from scripts.generate_synthetic_corp_data import build_scenario_s_ir
from src.ir_disclosure_auditor.ledger_fact_binder import DraftClaim, verify_ledger_fact_binding
from src.ir_disclosure_auditor.selective_disclosure_detector import audit_selective_disclosure


def test_scenario_s_ir_detects_selective_disclosure_and_generates_symmetric_rewrite() -> None:
    ledger, claims, card = build_scenario_s_ir()
    binding = verify_ledger_fact_binding(claims, ledger)
    assert binding.is_all_bound is True

    assert card.is_selective_washing_detected is True
    assert card.sdi_score > 1.5
    assert len(card.omitted_adverse_metrics) == 2
    assert "통상임금 미산입 우발부채 추계액" in card.layer_c_alert
    assert "[B층 대칭 공시 권고안]" in card.layer_b_symmetric_rewrite


def test_unbound_or_hallucinated_claim_triggers_layer_a_block() -> None:
    ledger, _, _ = build_scenario_s_ir()
    bad_claims = [
        DraftClaim(
            claim_id="CLM-HALLUCINATED",
            topic="human_capital_esg",
            sentence="당사의 2026년 여성 임원 비율은 45.0%로 업계 최고 수준입니다.",
            cited_metric_id="NON-EXISTENT-ID",
            stated_value=45.0,
        ),
        DraftClaim(
            claim_id="CLM-EXAGGERATED",
            topic="human_capital_esg",
            sentence="육아휴직 사용률 증가폭이 50.0%에 달했습니다.",
            cited_metric_id="HR-PAR-01",  # True value in ledger is 25.0%
            stated_value=50.0,
        ),
    ]
    res = verify_ledger_fact_binding(bad_claims, ledger)
    assert res.is_all_bound is False
    assert len(res.layer_a_unbound_blocks) == 2


def test_ir_c_layer_cannot_be_disabled() -> None:
    ledger, claims, _ = build_scenario_s_ir()
    with pytest.raises(PermissionError):
        audit_selective_disclosure("human_capital_esg", claims, ledger, allow_disable=True)
