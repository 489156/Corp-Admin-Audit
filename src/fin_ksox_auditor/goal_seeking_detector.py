"""Layer-C Goal-Seeking Manipulation Index (GSI) Detector for K-SOX Payroll & Severance Audits.

Detects when a practitioner or executive reverse-engineers payroll/provision parameters
(e.g., excluding regular bonuses from ordinary wage or lowering accrual rates) between initial
run (t0) and final run (t1) to force total cost delta under a target budget ceiling B_target.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import List

from src.fin_ksox_auditor.ledger_simulator import PayrollAuditResult, PayrollSimulationConfig


@dataclass(frozen=True)
class GoalSeekingAuditReport:
    initial_delta_tc_krw: float
    revised_delta_tc_krw: float
    target_budget_krw: float
    gsi_score: float
    is_goal_seeking_detected: bool
    c_layer_alerts: List[str]
    requires_i2_i3_signoff: bool


def evaluate_goal_seeking_manipulation(
    initial_result: PayrollAuditResult,
    revised_result: PayrollAuditResult,
    initial_config: PayrollSimulationConfig,
    revised_config: PayrollSimulationConfig,
    target_budget_krw: float,
    gsi_lower: float = 0.70,
    gsi_upper: float = 1.50,
    allow_disable: bool = False,
) -> GoalSeekingAuditReport:
    """Computes GSI and raises non-removable Layer-C alerts when budget reverse-engineering occurs."""
    if allow_disable:
        raise PermissionError("[C층 비활성화 금지 위반] K-SOX 예산 역산 조작 탐지(Layer C)는 비활성화할 수 없습니다.")

    tc_t0 = initial_result.total_delta_tc_krw
    tc_t1 = revised_result.total_delta_tc_krw
    excess_t0 = max(tc_t0 - target_budget_krw, 0.0)
    reduction = max(tc_t0 - tc_t1, 1.0)
    gsi = round(excess_t0 / reduction, 4) if (tc_t0 > target_budget_krw and tc_t0 > tc_t1) else 0.0

    alerts: List[str] = []
    parameter_tampered = False

    if initial_config.include_regular_bonus_in_ordinary_wage and not revised_config.include_regular_bonus_in_ordinary_wage:
        parameter_tampered = True
        alerts.append(
            "[C층 적발: W-251 역산 조작] 초기 산출 대비 확정 산출에서 정기상여금의 통상임금 산입 설정을 고의 해제하여 "
            "4대보험 및 퇴직급여 충당부채 전입액을 인위적으로 축소했습니다."
        )

    if (
        initial_config.retirement_accrual_rate is not None
        and revised_config.retirement_accrual_rate is not None
        and revised_config.retirement_accrual_rate < initial_config.retirement_accrual_rate
    ):
        parameter_tampered = True
        alerts.append(
            f"[C층 적발: 퇴직충당률 임의 하향] 퇴직급여 충당률을 "
            f"{initial_config.retirement_accrual_rate:.4f}에서 {revised_config.retirement_accrual_rate:.4f}로 축소했습니다."
        )

    is_detected = (
        tc_t0 > target_budget_krw
        and tc_t1 <= target_budget_krw
        and gsi_lower <= gsi <= gsi_upper
        and parameter_tampered
    )

    if is_detected:
        alerts.insert(
            0,
            f"🟥 [C층 적발: K-SOX 목표예산 역산 조작(이익조정) 의심] 초기 순증액({tc_t0:,.0f}원)이 예산 한도"
            f"({target_budget_krw:,.0f}원)를 초과하자 파라미터 조작으로 순증액을 {tc_t1:,.0f}원으로 축소함 "
            f"(역산조작지수 GSI = {gsi:.2f}). CFO의 I2/I3 독립 근거 입력 필수.",
        )

    return GoalSeekingAuditReport(
        initial_delta_tc_krw=tc_t0,
        revised_delta_tc_krw=tc_t1,
        target_budget_krw=target_budget_krw,
        gsi_score=gsi,
        is_goal_seeking_detected=is_detected,
        c_layer_alerts=alerts,
        requires_i2_i3_signoff=is_detected or bool(revised_result.w251_ordinary_wage_warnings),
    )
