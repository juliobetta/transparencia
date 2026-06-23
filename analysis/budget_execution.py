import sqlite3

import pandas as pd


def run(conn: sqlite3.Connection, year: int) -> pd.DataFrame:
    df = pd.read_sql_query(
        "SELECT ano, empresa, codigo, descricao, empenhado, dotacao_atualizada FROM despesas_por_orgao WHERE ano = ?",
        conn,
        params=(year,),
    )
    df["empenhado"] = pd.to_numeric(df["empenhado"].str.replace(",", "."), errors="coerce").fillna(0)
    df["dotacao_atualizada"] = pd.to_numeric(df["dotacao_atualizada"].str.replace(",", "."), errors="coerce").fillna(0)
    df["taxa_execucao"] = df.apply(
        lambda r: r["empenhado"] / r["dotacao_atualizada"] if r["dotacao_atualizada"] > 0 else 0,
        axis=1,
    )
    df["alerta"] = df["taxa_execucao"].apply(lambda t: "baixa" if t < 0.3 else ("excesso" if t > 1.0 else "normal"))
    return df
