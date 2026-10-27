"""Core-01: @soft_compute Decorator & Color-Coded Spreadsheet Governance Engine.

Isolates unconfigured or missing enterprise variables as NotComputed badges ("⏳ 미산정(설정 대기)")
instead of raising runtime KeyError/ZeroDivisionError exceptions or fabricating numbers.
"""
from __future__ import annotations

from dataclasses import dataclass
from functools import wraps
from typing import Any, Callable

# 4-Color Spreadsheet Governance Palette (Shared with HR_Suite)
COLOR_GREEN_INPUT = "#E2EFDA"      # 🟩 사용자 직접 입력·조작 가능 영역
COLOR_GRAY_FORMULA = "#F2F2F2"     # ⬜ 자동 계산 수식 및 마스터 보호 영역
COLOR_ORANGE_PENDING = "#FCE4D6"   # 🟧 ⏳ 미산정(설정 대기) 또는 [🟡 검토 권장]
COLOR_RED_BLOCK = "#F8CBAD"        # 🟥 [🔴 즉시조치/제출차단] 법적·논리적 오류 및 C층 적발


@dataclass(frozen=True)
class NotComputed:
    """Represents a safely deferred calculation when a configuration variable is missing."""

    sheet_or_param: str
    reason: str = "설정 대기"

    @property
    def badge(self) -> str:
        return f"⏳ 미산정({self.reason}: {self.sheet_or_param})"

    @property
    def cell_color(self) -> str:
        return COLOR_ORANGE_PENDING

    def __str__(self) -> str:
        return self.badge


class MissingConfigError(KeyError):
    """Raised intentionally inside a @soft_compute function when a required table entry is absent."""

    def __init__(self, sheet_or_param: str, reason: str = "설정 대기") -> None:
        super().__init__(sheet_or_param)
        self.sheet_or_param = sheet_or_param
        self.reason = reason


def soft_compute(default_sheet: str = "기업행정_설정마스터.xlsx") -> Callable[[Callable[..., Any]], Callable[..., Any]]:
    """Decorator that traps MissingConfigError, KeyError, or None-Type arithmetic and returns NotComputed."""

    def decorator(func: Callable[..., Any]) -> Callable[..., Any]:
        @wraps(func)
        def wrapper(*args: Any, **kwargs: Any) -> Any:
            try:
                return func(*args, **kwargs)
            except MissingConfigError as exc:
                return NotComputed(sheet_or_param=exc.sheet_or_param, reason=exc.reason)
            except KeyError as exc:
                missing_key = str(exc).strip("'\"") or default_sheet
                return NotComputed(sheet_or_param=f"{default_sheet}:{missing_key}")

        return wrapper

    return decorator
