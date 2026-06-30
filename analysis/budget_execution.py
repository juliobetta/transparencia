from typing import Any

import pandas as pd
from sqlalchemy import text


def run(conn: Any, year: int) -> pd.DataFrame:
    df = pd.read_sql_query(
        text(
            "SELECT ano, empresa, codigo, descricao, empenhado, dotacao_atualizada FROM despesas_por_orgao WHERE ano = :ano"
        ),
        conn,
        params={"ano": year},
    )
    df["empenhado"] = pd.to_numeric(df["empenhado"].str.replace(",", "."), errors="coerce").fillna(0)
    df["dotacao_atualizada"] = pd.to_numeric(df["dotacao_atualizada"].str.replace(",", "."), errors="coerce").fillna(0)
    df["taxa_execucao"] = df.apply(
        lambda r: r["empenhado"] / r["dotacao_atualizada"] if r["dotacao_atualizada"] > 0 else 0,
        axis=1,
    )
    df["alerta"] = df.apply(
        lambda r: (
            "N/D"
            if r["empenhado"] == 0 and r["dotacao_atualizada"] == 0 and r["taxa_execucao"] == 0
            else ("baixa" if r["taxa_execucao"] < 0.3 else ("excesso" if r["taxa_execucao"] > 1.0 else "normal"))
        ),
        axis=1,
    )
    return df


def summarize(df: pd.DataFrame) -> dict:
    return {
        "total_empenhado": float(df["empenhado"].sum()),
        "total_dotacao": float(df["dotacao_atualizada"].sum()),
    }


def top_organs_by_dotacao(df: pd.DataFrame, n: int = 10) -> pd.DataFrame:
    """Aggregate by organ, compute execution rate + alert, return top-n by dotação."""
    by_organ = df.groupby(["empresa", "descricao"], as_index=False).agg(
        empenhado=("empenhado", "sum"), dotacao_atualizada=("dotacao_atualizada", "sum")
    )
    by_organ["taxa_execucao"] = by_organ.apply(
        lambda r: r["empenhado"] / r["dotacao_atualizada"] if r["dotacao_atualizada"] > 0 else 0.0,
        axis=1,
    )
    by_organ["alerta"] = by_organ.apply(
        lambda r: (
            "N/D"
            if r["empenhado"] == 0 and r["dotacao_atualizada"] == 0
            else ("baixa" if r["taxa_execucao"] < 0.3 else ("excesso" if r["taxa_execucao"] > 1.0 else "normal"))
        ),
        axis=1,
    )
    return by_organ.nlargest(n, "dotacao_atualizada").copy()
