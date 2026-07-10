from typing import Any

import pandas as pd
from sqlalchemy import text

from analysis import fontes_receita


def _sum_col(conn: Any, table: str, col: str, year: int, root_only: bool = False) -> float:
    try:
        sql = f"SELECT {col} FROM {table} t WHERE t.ano = :ano"
        if root_only:
            sql += (
                f" AND NOT EXISTS ("
                f"SELECT 1 FROM {table} t2"
                f" WHERE t2.ano = :ano"
                f" AND t2.codigo != t.codigo"
                f" AND t.codigo LIKE RTRIM(t2.codigo, '0.') || '%%'"
                f" AND LENGTH(RTRIM(t2.codigo, '0.')) < LENGTH(RTRIM(t.codigo, '0.'))"
                f")"
            )
        df = pd.read_sql_query(text(sql), conn, params={"ano": year})
        if df.empty:
            return 0.0
        return float(pd.to_numeric(df[col].astype(str).str.replace(",", "."), errors="coerce").fillna(0).sum())
    except Exception:
        return 0.0


def run(conn: Any, years: list[int]) -> pd.DataFrame:
    records = []
    sorted_years = sorted(years)
    # Chama o módulo unificado de fontes de receita para obter as receitas de forma consolidada e DRY
    rev_df = fontes_receita.run(conn, sorted_years)
    rev_map = dict(zip(rev_df["ano"], rev_df["total_arrecadado"]))

    for year in sorted_years:
        total_gasto = _sum_col(conn, "despesas_por_orgao", "pago", year)
        total_folha = _sum_col(conn, "pessoal", "proventos", year)

        total_rec = rev_map.get(year, 0.0)
        receita = total_rec if total_rec > 0 else None
        restos = _sum_col(conn, "despesas_restos_pagar", "pago", year)

        records.append(
            {
                "ano": year,
                "total_gasto": total_gasto,
                "total_folha": total_folha,
                "total_receita": receita,
                "restos_a_pagar": restos,
            }
        )

    df = pd.DataFrame(records)
    for col in ["total_gasto", "total_folha", "total_receita", "restos_a_pagar"]:
        df[f"{col}_pct_change"] = df[col].pct_change() * 100
    return df


def gap_pressao_fiscal(df: pd.DataFrame) -> dict:
    """Retorna gap entre crescimento dos gastos e da receita, pronto para renderização em gráfico."""
    valid = df.dropna(subset=["total_gasto_pct_change"]).copy()
    valid = valid[~valid["total_gasto_pct_change"].isin([float("inf"), float("-inf")])]
    valid = valid.dropna(subset=["total_gasto_pct_change"])
    gap = [
        round(v, 2) for v in (valid["total_gasto_pct_change"] - valid["total_receita_pct_change"].fillna(0)).tolist()
    ]
    return {
        "anos": valid["ano"].tolist(),
        "gap": gap,
        "colors": ["#F44336" if v > 0 else "#4CAF50" for v in gap],
    }
