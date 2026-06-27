from typing import Any

import pandas as pd
from sqlalchemy import text


def _sum_col(conn: Any, table: str, col: str, year: int) -> float:
    try:
        df = pd.read_sql_query(text(f"SELECT {col} FROM {table} WHERE ano = :ano"), conn, params={"ano": year})
        if df.empty:
            return 0.0
        return float(pd.to_numeric(df[col].astype(str).str.replace(",", "."), errors="coerce").fillna(0).sum())
    except Exception:
        return 0.0


def run(conn: Any, years: list[int]) -> pd.DataFrame:
    records = []
    for year in sorted(years):
        total_gasto = _sum_col(conn, "despesas_por_orgao", "pago", year)
        total_folha = _sum_col(conn, "pessoal", "proventos", year)

        propria = _sum_col(conn, "receita_orcamentaria", "arrecadado_total", year)
        if propria == 0:
            propria = _sum_col(conn, "receita_orcamentaria", "arrecadado", year)

        uniao = _sum_col(conn, "receita_uniao", "arrecadado_total", year)
        if uniao == 0:
            uniao = _sum_col(conn, "receita_uniao", "arrecadado", year)

        estado = _sum_col(conn, "receita_estado", "arrecadado_total", year)
        if estado == 0:
            estado = _sum_col(conn, "receita_estado", "arrecadado", year)

        total = propria + uniao + estado
        receita = total if total > 0 else None
        restos = _sum_col(conn, "despesas_restos_pagar", "pago", year)
        if restos == 0:
            restos = _sum_col(conn, "despesas_restos_pagar", "valor", year)

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
