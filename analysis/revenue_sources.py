import sqlite3

import pandas as pd


def _sum_arrecadado(conn: sqlite3.Connection, table: str, year: int) -> float:
    df = pd.read_sql_query(f"SELECT arrecadado, previsao_atualizada FROM {table} WHERE ano = ?", conn, params=(year,))
    total = pd.to_numeric(df["arrecadado"].astype(str).str.replace(",", "."), errors="coerce").fillna(0).sum()
    if total == 0:
        total = (
            pd.to_numeric(df["previsao_atualizada"].astype(str).str.replace(",", "."), errors="coerce").fillna(0).sum()
        )
    return float(total)


def run(conn: sqlite3.Connection, years: list[int]) -> pd.DataFrame:
    records = []
    for year in years:
        propria = _sum_arrecadado(conn, "receita_orcamentaria", year)
        uniao = _sum_arrecadado(conn, "receita_uniao", year)
        estado = _sum_arrecadado(conn, "receita_estado", year)
        total = propria + uniao + estado
        pct = propria / total * 100 if total > 0 else 0
        records.append(
            {
                "ano": year,
                "receita_propria": propria,
                "transferencias_uniao": uniao,
                "transferencias_estado": estado,
                "total": total,
                "pct_propria": pct,
                "alerta_dependencia": bool(pct < 10),
            }
        )
    df = pd.DataFrame(records)
    df["alerta_dependencia"] = df["alerta_dependencia"].astype(object)
    return df
