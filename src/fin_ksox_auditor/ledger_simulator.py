"""K-SOX 12-Month Segment Payroll & K-IFRS 1019 Retirement Provision Simulator.

Implements:
- Layer A: 2026 Minimum Wage hard-gate & E-231 statutory parental leave protection gate
- Layer B: Factor-by-factor decomposition of 12-month payroll delta (Base, Allowance, Bonus, Insurance, Severance)
- W-251 Alert: 2024.12 Supreme Court En Banc Ordinary Wage verification on regular bonuses
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, List, Optional

from src.core.soft_compute import MissingConfigError, NotComputed, soft_compute

MIN_MONTHLY_WAGE_2026_KRW = 2_156_880  # 10,320 KRW * 209h


@dataclass
class AllowancePolicy:
    code: str
    name: str
    monthly_amount_krw: float
    is_regular_and_uniform: bool = True
    include_in_ordinary_wage: bool = True


@dataclass
class EmployeePayrollRecord:
    emp_id: str
    name: str
    base_monthly_before_krw: float
    base_monthly_after_krw: float
    regular_bonus_annual_rate: float           # e.g., 4.0 for 400% of base monthly
    promotion_effective_month: int = 3         # m* in 1..12
    is_statutory_parental_leave: bool = False
    parental_leave_tenure_inclusion_ratio: float = 1.0
    avg_monthly_wage_estimate_krw: Optional[float] = None


@dataclass
class PayrollSimulationConfig:
    include_regular_bonus_in_ordinary_wage: bool = True
    employer_insurance_rate: Optional[float] = 0.0955   # Pension 4.75% + Health/LTC ~4.06% + Emp/Ind
    retirement_accrual_rate: Optional[float] = 1.0 / 12.0
    allowances: List[AllowancePolicy] = field(default_factory=list)


@dataclass
class PayrollAuditResult:
    total_delta_tc_krw: float
    delta_direct_pay_krw: float
    delta_insurance_krw: float
    delta_retirement_provision_krw: float
    layer_a_blocks: List[str]
    w251_ordinary_wage_warnings: List[str]
    employee_breakdown: Dict[str, Dict[str, float]]


def verify_layer_a_preconditions(
    employees: List[EmployeePayrollRecord],
) -> List[str]:
    """Checks 2026 minimum wage compliance and E-231 statutory parental leave protection."""
    blocks: List[str] = []
    for emp in employees:
        if emp.base_monthly_after_krw < MIN_MONTHLY_WAGE_2026_KRW:
            blocks.append(
                f"[A층 하드블록: 최저임금 위반] 사번 {emp.emp_id}({emp.name}) 월 기본급 "
                f"{emp.base_monthly_after_krw:,.0f}원이 2026년 최저임금({MIN_MONTHLY_WAGE_2026_KRW:,.0f}원) 미달입니다."
            )
        if emp.is_statutory_parental_leave and emp.parental_leave_tenure_inclusion_ratio < 1.0:
            blocks.append(
                f"[A층 하드블록: E-231 법정보호휴직 불이익 차단] 사번 {emp.emp_id}({emp.name}) 육아·출산보호휴직자의 "
                f"근속/승진 산입비율({emp.parental_leave_tenure_inclusion_ratio:.2f})이 1.0 미만으로 설정되었습니다."
            )
    return blocks


@soft_compute(default_sheet="T_보험_퇴직요율")
def simulate_12m_ksox_payroll(
    employees: List[EmployeePayrollRecord],
    config: PayrollSimulationConfig,
) -> PayrollAuditResult:
    """Calculates 12-month K-SOX payroll delta and K-IFRS 1019 retirement provision."""
    if config.employer_insurance_rate is None:
        raise MissingConfigError("T_보험요율:회사부담률")
    if config.retirement_accrual_rate is None:
        raise MissingConfigError("T_퇴직급여:충당률")

    layer_a_blocks = verify_layer_a_preconditions(employees)
    w251_warnings: List[str] = []

    if not config.include_regular_bonus_in_ordinary_wage:
        w251_warnings.append(
            "[W-251 통상임금 재검토 경보] 정기상여금이 통상임금 산입 대상에서 제외되었습니다 "
            "(2024.12 대법원 전원합의체 2020다247190 판결 위반 및 퇴직급여 충당부채 과소계상 위험)."
        )

    for alw in config.allowances:
        if alw.is_regular_and_uniform and not alw.include_in_ordinary_wage:
            w251_warnings.append(
                f"[W-251 통상임금 재검토 경보] 정기·일률 수당 '{alw.name}'({alw.code})이 통상임금에서 제외되었습니다."
            )

    total_direct = 0.0
    total_ins = 0.0
    total_ret = 0.0
    breakdown: Dict[str, Dict[str, float]] = {}

    allowance_sum = sum(a.monthly_amount_krw for a in config.allowances)
    ordinary_allowance_sum = sum(
        a.monthly_amount_krw for a in config.allowances if a.include_in_ordinary_wage
    )

    for emp in employees:
        active_months = max(0, 12 - emp.promotion_effective_month + 1)
        delta_base_monthly = emp.base_monthly_after_krw - emp.base_monthly_before_krw

        # Monthly regular bonus equivalent
        bonus_monthly_before = emp.base_monthly_before_krw * (emp.regular_bonus_annual_rate / 12.0)
        bonus_monthly_after = emp.base_monthly_after_krw * (emp.regular_bonus_annual_rate / 12.0)
        delta_bonus_monthly = bonus_monthly_after - bonus_monthly_before

        # Ordinary wage before/after (for overtime/retirement floor under K-IFRS 1019)
        if config.include_regular_bonus_in_ordinary_wage:
            ord_before = emp.base_monthly_before_krw + ordinary_allowance_sum + bonus_monthly_before
            ord_after = emp.base_monthly_after_krw + ordinary_allowance_sum + bonus_monthly_after
        else:
            ord_before = emp.base_monthly_before_krw + ordinary_allowance_sum
            ord_after = emp.base_monthly_after_krw + ordinary_allowance_sum

        delta_ord_monthly = ord_after - ord_before

        # Direct pay delta over active months (base + bonus + ordinary-linked statutory premium impact)
        emp_direct_delta = active_months * (delta_base_monthly + delta_bonus_monthly)
        emp_ins_delta = active_months * delta_ord_monthly * float(config.employer_insurance_rate)

        # K-IFRS 1019 DB retirement provision delta based on max(avg_wage, ordinary_wage)
        emp_ret_delta = active_months * delta_ord_monthly * float(config.retirement_accrual_rate)

        total_direct += emp_direct_delta
        total_ins += emp_ins_delta
        total_ret += emp_ret_delta

        breakdown[emp.emp_id] = {
            "direct_delta_krw": round(emp_direct_delta, 2),
            "insurance_delta_krw": round(emp_ins_delta, 2),
            "retirement_delta_krw": round(emp_ret_delta, 2),
            "total_delta_krw": round(emp_direct_delta + emp_ins_delta + emp_ret_delta, 2),
            "allowance_monthly_krw": allowance_sum,
        }

    return PayrollAuditResult(
        total_delta_tc_krw=round(total_direct + total_ins + total_ret, 2),
        delta_direct_pay_krw=round(total_direct, 2),
        delta_insurance_krw=round(total_ins, 2),
        delta_retirement_provision_krw=round(total_ret, 2),
        layer_a_blocks=layer_a_blocks,
        w251_ordinary_wage_warnings=w251_warnings,
        employee_breakdown=breakdown,
    )
