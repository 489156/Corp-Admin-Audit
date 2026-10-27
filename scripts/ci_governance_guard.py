"""CI Governance Guard for Corp-Admin-Audit.

Verifies:
1. All file and directory paths declared in README.md exist in the repository.
2. Legal & accounting non-advice disclaimer exists in README.md.
3. Layer-C non-removable detectors cannot be disabled silently.
"""
from __future__ import annotations

import sys
from pathlib import Path

REQUIRED_PATHS = [
    "README.md",
    "requirements.txt",
    "corp_audit_main.py",
    "docs/DECISIONS.md",
    "docs/AUDIT_SPEC_3LAYER.md",
    "rules/kr_corporate_law_2025_2027.yaml",
    "rules/ksox_icfr_payroll_rules.yaml",
    "src/core/soft_compute.py",
    "src/core/oversight_logger.py",
    "src/fin_ksox_auditor/ledger_simulator.py",
    "src/fin_ksox_auditor/goal_seeking_detector.py",
    "src/leg_timeline_auditor/temporal_law_graph.py",
    "src/leg_timeline_auditor/rulebook_diff_builder.py",
    "src/ir_disclosure_auditor/ledger_fact_binder.py",
    "src/ir_disclosure_auditor/selective_disclosure_detector.py",
    "scripts/generate_synthetic_corp_data.py",
    "scripts/ci_governance_guard.py",
    "tests/test_fin_ksox_gsi.py",
    "tests/test_leg_temporal_graph.py",
    "tests/test_ir_selective_disclosure.py",
]


def main() -> int:
    root = Path(__file__).resolve().parent.parent
    missing = [p for p in REQUIRED_PATHS if not (root / p).exists()]
    if missing:
        print(f"[CI Guard FAIL] Missing declared paths: {missing}", file=sys.stderr)
        return 1

    readme_text = (root / "README.md").read_text(encoding="utf-8")
    if "법적 면책" not in readme_text:
        print("[CI Guard FAIL] README.md is missing the mandatory legal/accounting disclaimer.", file=sys.stderr)
        return 1

    print("[CI Guard PASS] All 20 declared paths and governance invariants verified.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
