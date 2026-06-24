from __future__ import annotations

from dataclasses import dataclass


@dataclass
class PeriodSpec:
    year: int
    month_start: int
    month_end: int

    def label(self) -> str:
        if self.month_start == 1 and self.month_end == 12:
            return str(self.year)
        return f"{self.year}/{self.month_start:02d}–{self.month_end:02d}"


def _delta(a: float, b: float) -> dict:
    return {
        "a": a,
        "b": b,
        "abs": b - a,
        "pct": (b - a) / a * 100 if a != 0 else None,
    }
