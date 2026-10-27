"""Layer-A Ledger-Bound Fact Verification for Generative AI Corporate IR & ESG Disclosures.

Binds every quantitative claim in a draft disclosure to an authenticated internal ledger metric
(with SHA-256 provenance). Unbound or mismatched numbers trigger an immediate Layer-A hard block.
"""
from __future__ import annotations

import hashlib
from dataclasses import dataclass
from typing import Dict, List, Optional


@dataclass(frozen=True)
class LedgerMetric:
    metric_id: str
    topic: str
    label_kr: str
    value: float
    unit: str
    z_score: float             # Standardized performance score (+ is favorable, - is adverse risk)
    source_sheet: str

    @property
    def ledger_hash(self) -> str:
        raw = f"{self.metric_id}:{self.value}:{self.unit}:{self.source_sheet}"
        return hashlib.sha256(raw.encode("utf-8")).hexdigest()[:16]


@dataclass(frozen=True)
class DraftClaim:
    claim_id: str
    topic: str
    sentence: str
    cited_metric_id: Optional[str]
    stated_value: float


@dataclass(frozen=True)
class FactBindingAuditResult:
    is_all_bound: bool
    layer_a_unbound_blocks: List[str]
    bound_claim_hashes: Dict[str, str]


def verify_ledger_fact_binding(
    claims: List[DraftClaim],
    ledger: Dict[str, LedgerMetric],
    tolerance: float = 1e-2,
) -> FactBindingAuditResult:
    """Verifies that every quantitative claim in the IR/ESG draft matches the internal ledger."""
    blocks: List[str] = []
    hashes: Dict[str, str] = {}

    for claim in claims:
        if not claim.cited_metric_id or claim.cited_metric_id not in ledger:
            blocks.append(
                f"🟥 [A층 차단: 원장 미연결 허위 수치] 문장({claim.claim_id}) '{claim.sentence}'의 수치"
                f"({claim.stated_value})가 사내 공식 원장(HR·재경·법무 DB)에 연결되어 있지 않습니다."
            )
            continue

        metric = ledger[claim.cited_metric_id]
        if abs(metric.value - claim.stated_value) > tolerance:
            blocks.append(
                f"🟥 [A층 차단: 원장 수치 불일치] 문장({claim.claim_id})의 표기 수치({claim.stated_value}{metric.unit})가 "
                f"원장 실제 수치({metric.value}{metric.unit}, 시트: {metric.source_sheet})와 일치하지 않습니다."
            )
            continue

        hashes[claim.claim_id] = metric.ledger_hash

    return FactBindingAuditResult(
        is_all_bound=(len(blocks) == 0),
        layer_a_unbound_blocks=blocks,
        bound_claim_hashes=hashes,
    )
