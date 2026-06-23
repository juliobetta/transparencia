import sqlite3

import pandas as pd


def _sum_col(conn: sqlite3.Connection, table: str, col: str, year: int) -> float:
    df = pd.read_sql_query(f"SELECT {col} FROM {table} WHERE ano = ?", conn, params=(year,))
    return pd.to_numeric(df[col].astype(str).str.replace(",", "."), errors="coerce").fillna(0).sum()


def run(conn: sqlite3.Connection, years: list[int]) -> pd.DataFrame:
    records = []
    for year in sorted(years):
        total_gasto = _sum_col(conn, "despesas_por_orgao", "pago", year)
        total_folha = _sum_col(conn, "pessoal", "remuneracao", year)
        receita = (
            _sum_col(conn, "receita_orcamentaria", "arrecadado", year)
            + _sum_col(conn, "receita_uniao", "arrecadado", year)
            + _sum_col(conn, "receita_estado", "arrecadado", year)
        )
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
