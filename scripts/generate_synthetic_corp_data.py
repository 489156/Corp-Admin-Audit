"""COI-Free Synthetic Enterprise Benchmark Generator (Scenarios S_FIN, S_LEG, S_IR).

Generates synthetic enterprise data and optionally builds `기업행정_설정마스터.xlsx`
so non-developer practitioners and researchers can verify all 3 audit modules in 1 second.
"""
from __future__ import annotations

from datetime import date
from pathlib import Path
from typing import Dict, List, Tuple

from src.fin_ksox_auditor.goal_seeking_detector import (
    GoalSeekingAuditReport,
    evaluate_goal_seeking_manipulation,
)
from src.fin_ksox_auditor.ledger_simulator import (
    AllowancePolicy,
    EmployeePayrollRecord,
    PayrollSimulationConfig,
    simulate_12m_ksox_payroll,
)
from src.ir_disclosure_auditor.ledger_fact_binder import DraftClaim, LedgerMetric
from src.ir_disclosure_auditor.selective_disclosure_detector import (
    SymmetricDisclosureCard,
    audit_selective_disclosure,
)
from src.leg_timeline_auditor.rulebook_diff_builder import (
    RulebookAuditReport,
    audit_corporate_rulebook,
)
from src.leg_timeline_auditor.temporal_law_graph import TemporalLegalGraph


def build_scenario_s_fin() -> GoalSeekingAuditReport:
    """Scenario S_FIN: Goal-seeking manipulation by excluding regular bonus from ordinary wage (W-251)."""
    employees: List[EmployeePayrollRecord] = [
        EmployeePayrollRecord(
            emp_id=f"EMP-{i:04d}",
            name=f"가상직원_{i:03d}",
            base_monthly_before_krw=4_000_000,
            base_monthly_after_krw=4_500_000,
            regular_bonus_annual_rate=4.0,  # 400% regular bonus
            promotion_effective_month=3,
        )
        for i in range(1, 51)
    ]

    # Initial honest K-SOX config (t0): includes regular bonus in ordinary wage
    config_t0 = PayrollSimulationConfig(
        include_regular_bonus_in_ordinary_wage=True,
        employer_insurance_rate=0.0955,
        retirement_accrual_rate=1.0 / 12.0,
        allowances=[AllowancePolicy("ALW-01", "직책수당", 300_000, True, True)],
    )
    # Tampered config (t1): excludes regular bonus from ordinary wage & lowers accrual rate to fit 368.75M budget
    config_t1 = PayrollSimulationConfig(
        include_regular_bonus_in_ordinary_wage=False,
        employer_insurance_rate=0.0955,
        retirement_accrual_rate=0.04,
        allowances=[AllowancePolicy("ALW-01", "직책수당", 300_000, True, False)],
    )

    res_t0 = simulate_12m_ksox_payroll(employees, config_t0)
    res_t1 = simulate_12m_ksox_payroll(employees, config_t1)

    return evaluate_goal_seeking_manipulation(
        initial_result=res_t0,
        revised_result=res_t1,
        initial_config=config_t0,
        revised_config=config_t1,
        target_budget_krw=368_750_000,
    )


def build_scenario_s_leg(rules_yaml_path: str | Path) -> RulebookAuditReport:
    """Scenario S_LEG: Outdated corporate rulebook audited as of 2026-10-25."""
    graph = TemporalLegalGraph.from_yaml(rules_yaml_path)
    sample_rulebook: Dict[str, str] = {
        "maternity_paternity": "배우자 출산휴가는 20일 유급으로 하며 3회 분할 가능하고 미숙아는 100일로 한다.",
        "minimum_wage": "2026년 최저임금은 시간급 10,320원(월 2,156,880원)을 준수한다.",
        # Missing short-term parental leave (effective 2026-08-20) -> Layer A block!
        "parental_leave_short": "만 8세 이하 자녀에 한하여 육아기 근로시간 단축을 허용한다.",
        # Missing spouse miscarriage leave & 50-day prior usage (effective 2026-09-18) -> Layer A block!
        "spouse_maternity_miscarriage": "출산한 날부터 배우자 출산휴가를 사용한다.",
        "wage_arrears_penalty": "임금 정기지급 및 통상임금 재검토를 시행한다.",
        # Upcoming 2026-11-27 subfertility leave still at 2 days paid -> Layer B advisory!
        "subfertility_and_harassment": "난임치료휴가는 연 6일(최초 2일 유급)을 부여한다.",
        "four_hour_break_exemption": "4시간 근무 시 근로자 요청으로 휴게시간 면제 가능.",
        "half_day_annual_leave": "반일(4시간 분할) 사용 및 불이익 처우 금지.",
    }
    return audit_corporate_rulebook(
        rulebook_clauses=sample_rulebook,
        graph=graph,
        audit_date=date(2026, 10, 25),
    )


def build_scenario_s_ir() -> Tuple[Dict[str, LedgerMetric], List[DraftClaim], SymmetricDisclosureCard]:
    """Scenario S_IR: Cherry-picking favorable parental leave usage while omitting post-return attrition & W-251 liability."""
    ledger: Dict[str, LedgerMetric] = {
        "HR-PAR-01": LedgerMetric(
            metric_id="HR-PAR-01",
            topic="human_capital_esg",
            label_kr="육아휴직 사용률 증가폭",
            value=25.0,
            unit="%",
            z_score=1.60,
            source_sheet="HR_Suite_원장!D14",
        ),
        "HR-PAR-02": LedgerMetric(
            metric_id="HR-PAR-02",
            topic="human_capital_esg",
            label_kr="육아휴직 복직 후 6개월 내 퇴사율",
            value=38.0,
            unit="%",
            z_score=-1.90,
            source_sheet="HR_Suite_원장!E14",
        ),
        "FIN-W251-01": LedgerMetric(
            metric_id="FIN-W251-01",
            topic="human_capital_esg",
            label_kr="통상임금 미산입 우발부채 추계액",
            value=4.2,
            unit="억원",
            z_score=-2.10,
            source_sheet="FIN_KSOX_원장!H22",
        ),
    }

    # Draft only cites the positive metric HR-PAR-01
    claims: List[DraftClaim] = [
        DraftClaim(
            claim_id="CLM-01",
            topic="human_capital_esg",
            sentence="당사는 가족친화 경영을 통해 2026년 육아휴직 사용률 증가폭 25.0%를 달성하였습니다.",
            cited_metric_id="HR-PAR-01",
            stated_value=25.0,
        )
    ]

    card = audit_selective_disclosure("human_capital_esg", claims, ledger)
    return ledger, claims, card


if __name__ == "__main__":
    root = Path(__file__).resolve().parent.parent
    s_fin = build_scenario_s_fin()
    s_leg = build_scenario_s_leg(root / "rules" / "kr_corporate_law_2025_2027.yaml")
    _, _, s_ir = build_scenario_s_ir()

    print("=== [Corp-Admin-Audit 합성 엔터프라이즈 벤치마크 1초 검증 완료] ===")
    print(f"1. [S_FIN 재경 역산조작 감사] GSI = {s_fin.gsi_score:.2f} | 탐지여부: {s_fin.is_goal_seeking_detected}")
    print(
        f"2. [S_LEG 법무 시간축 감사] A층 즉시개정 필수: {s_leg.layer_a_mandatory_count}건 | "
        f"B층 사전개정 권고: {s_leg.layer_b_upcoming_count}건"
    )
    print(f"3. [S_IR 공시 워싱 감사] SDI = +{s_ir.sdi_score:.2f}σ | 워싱탐지: {s_ir.is_selective_washing_detected}")
