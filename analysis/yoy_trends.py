import sqlite3

import pandas as pd


def _sum_col(conn: sqlite3.Connection, table: str, col: str, year: int) -> float:
    try:
        df = pd.read_sql_query(f"SELECT {col} FROM {table} WHERE ano = ?", conn, params=(year,))
        if df.empty:
            return 0.0
        return float(pd.to_numeric(df[col].astype(str).str.replace(",", "."), errors="coerce").fillna(0).sum())
    except Exception:
        return 0.0


def run(conn: sqlite3.Connection, years: list[int]) -> pd.DataFrame:
    records = []
    for year in sorted(years):
        total_gasto = _sum_col(conn, "despesas_por_orgao", "pago", year)
        total_folha = _sum_col(conn, "pessoal", "proventos", year)

        # Revenue summing using arrecadado_total or falling back to previsao_atualizada if collection is 0 (past years)
        propria = _sum_col(conn, "receita_orcamentaria", "arrecadado_total", year)
        if propria == 0:
            propria = _sum_col(conn, "receita_orcamentaria", "arrecadado", year)
        if propria == 0:
            propria = _sum_col(conn, "receita_orcamentaria", "previsao_atualizada", year)

        uniao = _sum_col(conn, "receita_uniao", "arrecadado_total", year)
        if uniao == 0:
            uniao = _sum_col(conn, "receita_uniao", "arrecadado", year)
        if uniao == 0:
            uniao = _sum_col(conn, "receita_uniao", "previsao_atualizada", year)

        estado = _sum_col(conn, "receita_estado", "arrecadado_total", year)
        if estado == 0:
            estado = _sum_col(conn, "receita_estado", "arrecadado", year)
        if estado == 0:
            estado = _sum_col(conn, "receita_estado", "previsao_atualizada", year)

        receita = propria + uniao + estado
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
