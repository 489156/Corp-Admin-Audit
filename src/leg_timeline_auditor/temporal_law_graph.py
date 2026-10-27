"""Point-in-Time Legal Knowledge Graph for 2025-2027 Sequential Corporate Law Amendments.

Eliminates temporal hallucination by deterministically branching on (effective_date <= audit_date):
- Already effective mandatory rules -> Layer-A Hard Block ("🟥 [즉시개정 필수]")
- Upcoming amendments (effective_date > audit_date) -> Layer-B Advisory ("🟧 [사전개정 권고]")
"""
from __future__ import annotations

from dataclasses import dataclass
from datetime import date
from pathlib import Path
from typing import Any, Dict, List

import yaml


@dataclass(frozen=True)
class LawAmendmentNode:
    rule_id: str
    statute: str
    topic: str
    effective_date: date
    is_mandatory: bool
    category: str
    required_keywords: List[str]
    legacy_violation_patterns: List[str]
    standard_clause_template: str


class TemporalLegalGraph:
    """Loads and evaluates point-in-time statutory rules against corporate rulebooks/contracts."""

    def __init__(self, nodes: List[LawAmendmentNode]) -> None:
        self.nodes = sorted(nodes, key=lambda n: (n.effective_date, n.rule_id))

    @classmethod
    def from_yaml(cls, yaml_path: str | Path) -> "TemporalLegalGraph":
        with open(yaml_path, "r", encoding="utf-8") as f:
            raw: Dict[str, Any] = yaml.safe_load(f)
        nodes: List[LawAmendmentNode] = []
        for item in raw.get("rules", []):
            eff = date.fromisoformat(str(item["effective_date"]))
            nodes.append(
                LawAmendmentNode(
                    rule_id=item["rule_id"],
                    statute=item["statute"],
                    topic=item["topic"],
                    effective_date=eff,
                    is_mandatory=bool(item.get("is_mandatory", True)),
                    category=item.get("category", "general"),
                    required_keywords=list(item.get("required_keywords", [])),
                    legacy_violation_patterns=list(item.get("legacy_violation_patterns", [])),
                    standard_clause_template=item.get("standard_clause_template", ""),
                )
            )
        return cls(nodes)

    def partition_by_audit_date(
        self, audit_date: date
    ) -> Dict[str, List[LawAmendmentNode]]:
        effective_now = [n for n in self.nodes if n.effective_date <= audit_date]
        upcoming = [n for n in self.nodes if n.effective_date > audit_date]
        return {"effective": effective_now, "upcoming": upcoming}
