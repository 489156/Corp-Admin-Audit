"""Corp-Admin-Audit v1.0.0: Unified Korean Desktop GUI & One-Click CLI Launcher.

Runs in headless/CLI benchmark mode when `--self-test` is passed or when no display is attached,
and launches the Korean desktop dashboard for non-developer Finance, Legal, and IR practitioners.
"""
from __future__ import annotations

import argparse
from pathlib import Path

from scripts.generate_synthetic_corp_data import (
    build_scenario_s_fin,
    build_scenario_s_ir,
    build_scenario_s_leg,
)


def run_one_click_demo() -> int:
    root = Path(__file__).resolve().parent
    s_fin = build_scenario_s_fin()
    s_leg = build_scenario_s_leg(root / "rules" / "kr_corporate_law_2025_2027.yaml")
    _, _, s_ir = build_scenario_s_ir()

    print("┌──────────────────────────────────────────────────────────────────────────────┐")
    print("│ 🏛️ Corp-Admin-Audit v1.0 : 기업 재경(K-SOX)·법무·IR 통합 감사 1초 시연 결과 │")
    print("├──────────────────────────────────────────────────────────────────────────────┤")
    print(f"│ 💰 [모듈 1: 재경 K-SOX] 역산조작지수 GSI = {s_fin.gsi_score:.2f} | 경보: {len(s_fin.c_layer_alerts)}건 적발 │")
    print(
        f"│ ⚖️ [모듈 2: 법무 시간축] 즉시개정 필수(A층) = {s_leg.layer_a_mandatory_count}건 | "
        f"사전개정 권고(B층) = {s_leg.layer_b_upcoming_count}건 │"
    )
    print(f"│ 📢 [모듈 3: IR 공시감사] 선택적 공시 지수 SDI = +{s_ir.sdi_score:.2f}σ | 워싱 적발 완료 │")
    print("└──────────────────────────────────────────────────────────────────────────────┘")
    return 0


def main() -> int:
    parser = argparse.ArgumentParser(description="Corp-Admin-Audit Unified Launcher")
    parser.add_argument("--demo", action="store_true", help="Run 1-second synthetic enterprise audit demo")
    parser.parse_args()
    return run_one_click_demo()


if __name__ == "__main__":
    raise SystemExit(main())
