import sqlite3

import pandas as pd


def run(conn: sqlite3.Connection, year: int) -> dict:
    df = pd.read_sql_query(
        "SELECT codigo, descricao, empenhado FROM despesas_por_fornecedor WHERE ano = ?", conn, params=(year,)
    )
    df["empenhado"] = pd.to_numeric(df["empenhado"].str.replace(",", "."), errors="coerce").fillna(0)
    df = df.groupby(["codigo", "descricao"], as_index=False)["empenhado"].sum()
    total = df["empenhado"].sum()
    df["percentual"] = df["empenhado"] / total * 100 if total > 0 else 0
    top10 = df.nlargest(10, "empenhado").reset_index(drop=True)

    shares = df["empenhado"] / total if total > 0 else df["empenhado"] * 0
    hhi = float((shares**2).sum() * 10000)

    dominant_row = df[df["percentual"] > 40]
    dominante = dominant_row.iloc[0]["descricao"] if not dominant_row.empty else None

    return {"top10": top10, "hhi": hhi, "dominante": dominante}
