from __future__ import annotations

from dataclasses import dataclass
from typing import Any

import pandas as pd

from analysis import (
    adesao_de_ata,
    bidding_gaps,
    budget_execution,
    payroll_vs_services,
    revenue_sources,
    supplier_concentration,
)


@dataclass
class PeriodSpec:
    year: int
    month_start: int
    month_end: int

    def __post_init__(self) -> None:
        if self.month_start < 1:
            raise ValueError(f"month_start must be >= 1, got {self.month_start}")
        if self.month_end > 12:
            raise ValueError(f"month_end must be <= 12, got {self.month_end}")
        if self.month_start > self.month_end:
            raise ValueError(f"month_start ({self.month_start}) must be <= month_end ({self.month_end})")

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


def _filter_months(df: pd.DataFrame, month_col: str, spec: PeriodSpec) -> pd.DataFrame:
    months = {f"{m:02d}" for m in range(spec.month_start, spec.month_end + 1)}
    return df[df[month_col].astype(str).str.zfill(2).isin(months)]


def _get_revenue_row(df: pd.DataFrame, year: int) -> pd.Series | None:
    rows = df[df["ano"] == year]
    return rows.iloc[0] if not rows.empty else None


def run(conn: Any, spec_a: PeriodSpec, spec_b: PeriodSpec) -> dict:
    def _despesas(spec: PeriodSpec) -> dict:
        budget = budget_execution.run(conn, spec.year)
        return {
            "empenhado": budget["empenhado"].sum(),
            "dotacao": budget["dotacao_atualizada"].sum(),
        }

    def _pessoal(spec: PeriodSpec) -> dict:
        df = payroll_vs_services.run(conn, [spec.year])
        if df.empty:
            return {"total_folha": 0.0, "percentual_folha": 0.0}
        row = df.iloc[0]
        return {"total_folha": float(row["total_folha"]), "percentual_folha": float(row["percentual_folha"])}

    def _receitas(spec: PeriodSpec) -> dict:
        df = revenue_sources.run(conn, [spec.year])
        row = _get_revenue_row(df, spec.year)
        if row is None:
            return {
                "receita_propria": 0.0,
                "transferencias_uniao": 0.0,
                "transferencias_estado": 0.0,
                "total": 0.0,
                "pct_propria": 0.0,
            }
        return {
            "receita_propria": float(row["receita_propria"]),
            "transferencias_uniao": float(row["transferencias_uniao"]),
            "transferencias_estado": float(row["transferencias_estado"]),
            "total": float(row["total"]),
            "pct_propria": float(row["pct_propria"]),
        }

    def _licitacoes(spec: PeriodSpec) -> dict:
        gaps = bidding_gaps.run(conn, spec.year)
        return {
            "sem_licitacao": float(len(gaps)),
            "acima_limite": float(gaps["acima_limite"].sum()),
            "saude": float((gaps["acima_limite"] & gaps["orgao_saude"]).sum()),
        }

    def _fornecedores(spec: PeriodSpec) -> dict:
        result = supplier_concentration.run(conn, spec.year)
        return {"hhi": float(result["hhi"])}

    def _adesao(spec: PeriodSpec) -> dict:
        result = adesao_de_ata.run(conn, spec.year, "2")
        return {
            "count": float(result["count"]),
            "valor_licitacao": float(result["total_licitacao"]),
            "valor_contratos": float(result["value"]),
        }

    domains = [
        ("despesas", _despesas),
        ("pessoal", _pessoal),
        ("receitas", _receitas),
        ("licitacoes", _licitacoes),
        ("fornecedores", _fornecedores),
        ("adesao", _adesao),
    ]

    result: dict = {"spec_a": spec_a, "spec_b": spec_b}
    for name, fn in domains:
        a_vals = fn(spec_a)
        b_vals = fn(spec_b)
        result[name] = {k: _delta(a_vals[k], b_vals[k]) for k in a_vals}

    return result
