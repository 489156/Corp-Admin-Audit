"""Tests for Module 1 (FIN-1): K-SOX Payroll Simulator, @soft_compute, W-251, GSI, and I2/I3 Gate."""
from __future__ import annotations

import pytest

from scripts.generate_synthetic_corp_data import build_scenario_s_fin
from src.core.oversight_logger import RubberStampBlockedError, SubstantiveOversightLogger
from src.core.soft_compute import NotComputed
from src.fin_ksox_auditor.goal_seeking_detector import evaluate_goal_seeking_manipulation
from src.fin_ksox_auditor.ledger_simulator import (
    EmployeePayrollRecord,
    PayrollSimulationConfig,
    simulate_12m_ksox_payroll,
)


def test_scenario_s_fin_detects_goal_seeking_and_w251() -> None:
    report = build_scenario_s_fin()
    assert report.is_goal_seeking_detected is True
    assert 0.70 <= report.gsi_score <= 1.20
    assert report.requires_i2_i3_signoff is True
    assert any("W-251" in alert for alert in report.c_layer_alerts)


def test_soft_compute_returns_not_computed_badge_when_rate_missing() -> None:
    emp = EmployeePayrollRecord("EMP-01", "홍길동", 3_000_000, 3_500_000, 2.0)
    cfg = PayrollSimulationConfig(employer_insurance_rate=None)
    result = simulate_12m_ksox_payroll([emp], cfg)
    assert isinstance(result, NotComputed)
    assert "⏳ 미산정" in result.badge


def test_layer_a_blocks_minimum_wage_and_parental_leave_penalty() -> None:
    emp = EmployeePayrollRecord(
        emp_id="EMP-LOW",
        name="김미달",
        base_monthly_before_krw=2_000_000,
        base_monthly_after_krw=2_100_000,  # Below 2,156,880 KRW
        regular_bonus_annual_rate=1.0,
        is_statutory_parental_leave=True,
        parental_leave_tenure_inclusion_ratio=0.5,  # Violates E-231 (must be 1.0)
    )
    res = simulate_12m_ksox_payroll([emp], PayrollSimulationConfig())
    assert len(res.layer_a_blocks) == 2
    assert any("최저임금 위반" in b for b in res.layer_a_blocks)
    assert any("E-231" in b for b in res.layer_a_blocks)


def test_c_layer_cannot_be_disabled_and_i2_i3_blocks_rubber_stamping() -> None:
    emp = [EmployeePayrollRecord("EMP-01", "홍길동", 3_000_000, 3_500_000, 2.0)]
    cfg = PayrollSimulationConfig()
    res = simulate_12m_ksox_payroll(emp, cfg)

    with pytest.raises(PermissionError):
        evaluate_goal_seeking_manipulation(res, res, cfg, cfg, 10_000_000, allow_disable=True)

    logger = SubstantiveOversightLogger()
    with pytest.raises(RubberStampBlockedError):
        logger.record_signoff("FIN-KSOX", "CFO", "C-FIN-GSI", "확인함", "문제없음")

    rec = logger.record_signoff(
        domain="FIN-KSOX",
        actor_role="CFO",
        alert_code="C-FIN-GSI",
        i2_independent_evidence="삼일회계법인 외부자문 의견서(#2026-09)에 따른 단계적 충당 반영 근거 확인",
        i3_remediation_plan="2026년 4분기 추경 예산에 통상임금 산입 차액 충당부채 100% 반영 확약",
    )
    assert len(rec.record_hash) == 64
    assert logger.verify_chain_integrity() is True
