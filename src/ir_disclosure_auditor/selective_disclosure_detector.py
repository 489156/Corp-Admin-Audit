"""Layer-B & Layer-C Selective Disclosure & Washing Detector (SDI) for IR and ESG Reports.

Computes the Selective Disclosure Index (SDI):
  SDI_d = mean(z_{cited}) - mean(z_{all})
If SDI_d > +1.0 sigma AND critical adverse indicators (z < -1.5 sigma) in the same topic are
omitted from the draft, triggers a non-removable Layer-C washing alert and generates a
Layer-B symmetric disclosure recommendation.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, List

from src.ir_disclosure_auditor.ledger_fact_binder import DraftClaim, LedgerMetric


@dataclass(frozen=True)
class SymmetricDisclosureCard:
    topic: str
    sdi_score: float
    is_selective_washing_detected: bool
    cited_favorable_metrics: List[str]
    omitted_adverse_metrics: List[str]
    layer_c_alert: str
    layer_b_symmetric_rewrite: str


def audit_selective_disclosure(
    topic: str,
    claims: List[DraftClaim],
    ledger: Dict[str, LedgerMetric],
    sdi_threshold: float = 1.0,
    adverse_z_cutoff: float = -1.5,
    allow_disable: bool = False,
) -> SymmetricDisclosureCard:
    """Audits a disclosure topic for cherry-picking / ESG & IR washing."""
    if allow_disable:
        raise PermissionError("[C층 비활성화 금지 위반] IR 선택적 공시·워싱 탐지기(Layer C)는 비활성화할 수 없습니다.")

    topic_metrics = [m for m in ledger.values() if m.topic == topic]
    if not topic_metrics:
        return SymmetricDisclosureCard(
            topic=topic,
            sdi_score=0.0,
            is_selective_washing_detected=False,
            cited_favorable_metrics=[],
            omitted_adverse_metrics=[],
            layer_c_alert="",
            layer_b_symmetric_rewrite="",
        )

    cited_ids = {
        c.cited_metric_id for c in claims if c.topic == topic and c.cited_metric_id in ledger
    }
    cited_metrics = [m for m in topic_metrics if m.metric_id in cited_ids]

    mean_all = sum(m.z_score for m in topic_metrics) / len(topic_metrics)
    mean_cited = (
        sum(m.z_score for m in cited_metrics) / len(cited_metrics)
        if cited_metrics
        else mean_all
    )
    sdi = round(mean_cited - mean_all, 4)

    omitted_adverse = [
        m for m in topic_metrics if m.metric_id not in cited_ids and m.z_score <= adverse_z_cutoff
    ]

    is_washing = (sdi > sdi_threshold) and (len(omitted_adverse) > 0)

    favorable_labels = [f"{m.label_kr} ({m.value}{m.unit}, z={m.z_score:+.2f}σ)" for m in cited_metrics]
    omitted_labels = [f"{m.label_kr} ({m.value}{m.unit}, z={m.z_score:+.2f}σ)" for m in omitted_adverse]

    if is_washing:
        c_alert = (
            f"🟥 [C층 적발: 선택적 공시(Cherry-Picking) 및 워싱 의심] 토픽 '{topic}'의 선택적 공시 지수 "
            f"SDI = +{sdi:.2f}σ (기준 +{sdi_threshold:.2f}σ 초과). 원장 내 중대 리스크 지표 "
            f"{len(omitted_adverse)}건({', '.join(m.label_kr for m in omitted_adverse)})이 고의 누락되었습니다."
        )
        b_rewrite = (
            f"[B층 대칭 공시 권고안] '{topic}' 공시 시 긍정 지표({', '.join(favorable_labels)})와 함께 "
            f"사내 원장에 확인된 리스크 지표({', '.join(omitted_labels)}) 및 이에 대한 개선·충당 계획을 "
            f"동일 문단 또는 주석에 대칭적으로 병기하십시오."
        )
    else:
        c_alert = ""
        b_rewrite = "🟢 [적정 공시] 원장 지표 분포와 공시 채택 지표 간 유의미한 편향이 탐지되지 않았습니다."

    return SymmetricDisclosureCard(
        topic=topic,
        sdi_score=sdi,
        is_selective_washing_detected=is_washing,
        cited_favorable_metrics=favorable_labels,
        omitted_adverse_metrics=omitted_labels,
        layer_c_alert=c_alert,
        layer_b_symmetric_rewrite=b_rewrite,
    )
