"""Substantive Human Oversight Gate (I2/I3) & Immutable SHA-256 Hash-Chain Audit Logger.

Prevents rubber-stamping by requiring CFO / CLO / IRO sign-off to supply:
- I2: Independent external evidence (outside the AI report text, >= 20 chars)
- I3: Counter-argument / concrete remediation plan (>= 20 chars)
"""
from __future__ import annotations

import hashlib
import json
from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from typing import Dict, List, Optional


class RubberStampBlockedError(ValueError):
    """Raised when an executive attempts to override a Layer-C or Layer-A alert without substantive I2/I3."""


@dataclass(frozen=True)
class OversightSignOffRecord:
    sequence: int
    timestamp_utc: str
    domain: str               # "FIN-KSOX" | "LEG-TIMELINE" | "IR-DISCLOSURE"
    actor_role: str           # e.g., "CFO", "CLO", "IRO"
    alert_code: str           # e.g., "C-FIN-GSI", "W-251", "C-IR-SDI"
    i2_independent_evidence: str
    i3_remediation_plan: str
    prev_hash: str
    record_hash: str


class SubstantiveOversightLogger:
    """Append-only SHA-256 hash-chain logger enforcing I2/I3 substantive human oversight."""

    MIN_RATIONALE_LENGTH = 20
    BANNED_RUBBER_STAMP_PHRASES = (
        "확인함",
        "문제없음",
        "승인함",
        "원안대로",
        "특이사항 없음",
        "ai 결과 동의",
    )

    def __init__(self, min_length: int = MIN_RATIONALE_LENGTH) -> None:
        self.min_length = min_length
        self._chain: List[OversightSignOffRecord] = []

    @property
    def chain(self) -> List[OversightSignOffRecord]:
        return list(self._chain)

    def _validate_substantive_text(self, field_name: str, text: str, report_excerpt: str = "") -> str:
        cleaned = (text or "").strip()
        if len(cleaned) < self.min_length:
            raise RubberStampBlockedError(
                f"[{field_name} 고무도장 결재 차단] 최소 {self.min_length}자 이상의 구체적 사유를 기재해야 합니다 (현재 {len(cleaned)}자)."
            )
        lowered = cleaned.lower()
        for phrase in self.BANNED_RUBBER_STAMP_PHRASES:
            if lowered == phrase:
                raise RubberStampBlockedError(
                    f"[{field_name} 고무도장 결재 차단] 상투적 문구('{phrase}')만으로는 예외 결재를 진행할 수 없습니다."
                )
        if report_excerpt and cleaned == report_excerpt.strip():
            raise RubberStampBlockedError(
                f"[{field_name} 고무도장 결재 차단] AI 리포트 문구를 그대로 복사·붙여넣기한 내용은 독립 근거(I2)로 인정되지 않습니다."
            )
        return cleaned

    def record_signoff(
        self,
        domain: str,
        actor_role: str,
        alert_code: str,
        i2_independent_evidence: str,
        i3_remediation_plan: str,
        report_excerpt: str = "",
        timestamp_override: Optional[str] = None,
    ) -> OversightSignOffRecord:
        i2_clean = self._validate_substantive_text("I2(독립 판단 근거)", i2_independent_evidence, report_excerpt)
        i3_clean = self._validate_substantive_text("I3(사후 보완 계획)", i3_remediation_plan, report_excerpt)

        seq = len(self._chain) + 1
        prev_hash = self._chain[-1].record_hash if self._chain else "0" * 64
        ts = timestamp_override or datetime.now(timezone.utc).isoformat()

        payload: Dict[str, object] = {
            "sequence": seq,
            "timestamp_utc": ts,
            "domain": domain,
            "actor_role": actor_role,
            "alert_code": alert_code,
            "i2_independent_evidence": i2_clean,
            "i3_remediation_plan": i3_clean,
            "prev_hash": prev_hash,
        }
        digest = hashlib.sha256(
            json.dumps(payload, ensure_ascii=False, sort_keys=True).encode("utf-8")
        ).hexdigest()

        record = OversightSignOffRecord(
            sequence=seq,
            timestamp_utc=ts,
            domain=domain,
            actor_role=actor_role,
            alert_code=alert_code,
            i2_independent_evidence=i2_clean,
            i3_remediation_plan=i3_clean,
            prev_hash=prev_hash,
            record_hash=digest,
        )
        self._chain.append(record)
        return record

    def verify_chain_integrity(self) -> bool:
        prev_hash = "0" * 64
        for rec in self._chain:
            if rec.prev_hash != prev_hash:
                return False
            payload = asdict(rec)
            expected_hash = payload.pop("record_hash")
            recomputed = hashlib.sha256(
                json.dumps(payload, ensure_ascii=False, sort_keys=True).encode("utf-8")
            ).hexdigest()
            if recomputed != expected_hash:
                return False
            prev_hash = expected_hash
        return True
