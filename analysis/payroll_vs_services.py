import sqlite3

import pandas as pd


def run(conn: sqlite3.Connection, years: list[int]) -> pd.DataFrame:
    records = []
    for year in years:
        folha = pd.read_sql_query("SELECT remuneracao FROM pessoal WHERE ano = ?", conn, params=(year,))
        total_folha = pd.to_numeric(folha["remuneracao"].str.replace(",", "."), errors="coerce").fillna(0).sum()

        gasto = pd.read_sql_query("SELECT pago FROM despesas_por_orgao WHERE ano = ?", conn, params=(year,))
        total_gasto = pd.to_numeric(gasto["pago"].str.replace(",", "."), errors="coerce").fillna(0).sum()

        percentual = total_folha / total_gasto * 100 if total_gasto > 0 else 0
        records.append(
            {"ano": year, "total_folha": total_folha, "total_gasto": total_gasto, "percentual_folha": percentual}
        )
    return pd.DataFrame(records)
