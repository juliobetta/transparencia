from typing import Any

import pandas as pd
from sqlalchemy import text


def run(conn: Any, year: int, empresa_ids: list[str] | None = None) -> pd.DataFrame:
    empresa_clause = "AND empresa = ANY(:empresas)" if empresa_ids else ""
    params: dict = {"ano": year}
    if empresa_ids:
        params["empresas"] = empresa_ids
    df = pd.read_sql_query(
        text(
            f"SELECT ano, empresa, codigo, descricao, empenhado, liquidado, pago, dotacao_atualizada FROM despesas_por_orgao WHERE ano = :ano {empresa_clause}"
        ),
        conn,
        params=params,
    )
    df["empenhado"] = pd.to_numeric(df["empenhado"].str.replace(",", "."), errors="coerce").fillna(0)
    df["liquidado"] = pd.to_numeric(df["liquidado"].str.replace(",", "."), errors="coerce").fillna(0)
    df["pago"] = pd.to_numeric(df["pago"].str.replace(",", "."), errors="coerce").fillna(0)
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
    total_dotacao = float(df["dotacao_atualizada"].sum())
    total_empenhado = float(df["empenhado"].sum())
    total_liquidado = float(df["liquidado"].sum())
    total_pago = float(df["pago"].sum())
    return {
        "total_empenhado": total_empenhado,
        "total_liquidado": total_liquidado,
        "total_pago": total_pago,
        "total_dotacao": total_dotacao,
        "saldo_orcamentario": total_dotacao - total_empenhado,
    }


def top_orgaos_por_dotacao(df: pd.DataFrame, n: int = 10) -> pd.DataFrame:
    """Agregar por órgão, calcular taxa de execução + alerta, retornar top-n por dotação."""
    por_orgao = df.groupby(["empresa", "descricao"], as_index=False).agg(
        empenhado=("empenhado", "sum"), dotacao_atualizada=("dotacao_atualizada", "sum")
    )
    por_orgao["taxa_execucao"] = por_orgao.apply(
        lambda r: r["empenhado"] / r["dotacao_atualizada"] if r["dotacao_atualizada"] > 0 else 0.0,
        axis=1,
    )
    por_orgao["alerta"] = por_orgao.apply(
        lambda r: (
            "N/D"
            if r["empenhado"] == 0 and r["dotacao_atualizada"] == 0
            else ("baixa" if r["taxa_execucao"] < 0.3 else ("excesso" if r["taxa_execucao"] > 1.0 else "normal"))
        ),
        axis=1,
    )
    return por_orgao.nlargest(n, "dotacao_atualizada").copy()


def summarize_by_year(conn: Any, years: list[int], empresa_ids: list[str] | None = None) -> dict[int, dict]:
    return {year: summarize(run(conn, year, empresa_ids=empresa_ids)) for year in years}
