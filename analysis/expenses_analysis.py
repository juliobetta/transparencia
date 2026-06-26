from typing import Any

import pandas as pd
from sqlalchemy import text


def _sum_col_where(conn: Any, table: str, col: str, year: int) -> float:
    try:
        df = pd.read_sql_query(text(f"SELECT {col} FROM {table} WHERE ano = :ano"), conn, params={"ano": year})
        if df.empty:
            return 0.0
        return float(pd.to_numeric(df[col].astype(str).str.replace(",", "."), errors="coerce").fillna(0).sum())
    except Exception:
        return 0.0


def get_general_expense_metrics(conn: Any, year: int) -> dict:
    empenhado = _sum_col_where(conn, "despesas_por_unidade", "empenhado", year)
    liquidado = _sum_col_where(conn, "despesas_por_unidade", "liquidado", year)
    pago = _sum_col_where(conn, "despesas_por_unidade", "pago", year)

    return {
        "empenhado": empenhado,
        "liquidado": liquidado,
        "pago": pago,
        "taxa_liquidacao": (liquidado / empenhado * 100) if empenhado > 0 else 0.0,
        "taxa_pagamento": (pago / empenhado * 100) if empenhado > 0 else 0.0,
    }


def get_expenses_by_unit(conn: Any, year: int) -> pd.DataFrame:
    df = pd.read_sql_query(
        text(
            "SELECT codigo, descricao, empenhado, liquidado, pago, dotacao_atualizada FROM despesas_por_unidade WHERE ano = :ano"
        ),
        conn,
        params={"ano": year},
    )
    if df.empty:
        return pd.DataFrame(columns=["descricao", "empenhado", "liquidado", "pago", "dotacao_atualizada"])

    df["empenhado"] = pd.to_numeric(df["empenhado"].str.replace(",", "."), errors="coerce").fillna(0)
    df["liquidado"] = pd.to_numeric(df["liquidado"].str.replace(",", "."), errors="coerce").fillna(0)
    df["pago"] = pd.to_numeric(df["pago"].str.replace(",", "."), errors="coerce").fillna(0)
    df["dotacao_atualizada"] = pd.to_numeric(df["dotacao_atualizada"].str.replace(",", "."), errors="coerce").fillna(0)

    return (
        df.groupby("descricao", as_index=False)[["empenhado", "liquidado", "pago", "dotacao_atualizada"]]
        .sum()
        .sort_values("pago", ascending=False)
    )


def get_top_suppliers_detailed(conn: Any, year: int) -> pd.DataFrame:
    df = pd.read_sql_query(
        text(
            "SELECT descricao as fornecedor, insmf, cepci as cidade, empenhado, liquidado, pago FROM despesas_por_fornecedor WHERE ano = :ano"
        ),
        conn,
        params={"ano": year},
    )
    if df.empty:
        return pd.DataFrame(columns=["fornecedor", "insmf", "cidade", "empenhado", "liquidado", "pago"])

    df["empenhado"] = pd.to_numeric(df["empenhado"].str.replace(",", "."), errors="coerce").fillna(0)
    df["liquidado"] = pd.to_numeric(df["liquidado"].str.replace(",", "."), errors="coerce").fillna(0)
    df["pago"] = pd.to_numeric(df["pago"].str.replace(",", "."), errors="coerce").fillna(0)

    return (
        df.groupby(["fornecedor", "insmf", "cidade"], as_index=False)[["empenhado", "liquidado", "pago"]]
        .sum()
        .sort_values("pago", ascending=False)
    )


def get_local_spending_impact(conn: Any, year: int) -> dict:
    df = pd.read_sql_query(
        text("SELECT cepci as cidade, pago FROM despesas_por_fornecedor WHERE ano = :ano"),
        conn,
        params={"ano": year},
    )
    if df.empty:
        return {"local_pago": 0.0, "externo_pago": 0.0, "total_pago": 0.0, "pct_local": 0.0}

    df["pago"] = pd.to_numeric(df["pago"].str.replace(",", "."), errors="coerce").fillna(0)
    df["cidade_clean"] = df["cidade"].fillna("").astype(str).str.strip().str.upper()

    is_local = df["cidade_clean"] == "PORCIUNCULA"
    local_pago = df[is_local]["pago"].sum()
    externo_pago = df[~is_local]["pago"].sum()
    total_pago = local_pago + externo_pago

    return {
        "local_pago": float(local_pago),
        "externo_pago": float(externo_pago),
        "total_pago": float(total_pago),
        "pct_local": (local_pago / total_pago * 100) if total_pago > 0 else 0.0,
    }


def get_diarias_summary(conn: Any, year: int) -> dict:
    df = pd.read_sql_query(text("SELECT valor, favorecido FROM diarias WHERE ano = :ano"), conn, params={"ano": year})
    if df.empty:
        return {"total_valor": 0.0, "total_viajantes": 0, "media_reembolso": 0.0}

    df["valor"] = pd.to_numeric(df["valor"].str.replace(",", "."), errors="coerce").fillna(0)
    total_valor = df["valor"].sum()
    total_viajantes = df["favorecido"].nunique()

    return {
        "total_valor": float(total_valor),
        "total_viajantes": int(total_viajantes),
        "media_reembolso": (total_valor / len(df)) if len(df) > 0 else 0.0,
    }


def get_top_diarias_beneficiaries(conn: Any, year: int) -> pd.DataFrame:
    df = pd.read_sql_query(
        text("SELECT favorecido, cargo, valor FROM diarias WHERE ano = :ano"), conn, params={"ano": year}
    )
    if df.empty:
        return pd.DataFrame(columns=["favorecido", "cargo", "valor", "viagens"])

    df["valor"] = pd.to_numeric(df["valor"].str.replace(",", "."), errors="coerce").fillna(0)

    summary = df.groupby(["favorecido", "cargo"], as_index=False).agg(
        valor=("valor", "sum"), viagens=("valor", "count")
    )
    return summary.sort_values("valor", ascending=False).head(10)


def get_searchable_transactions(conn: Any, year: int, query: str, limit: int = 500) -> pd.DataFrame:
    if query.strip():
        sql = text("""
            SELECT datae as data, nomefor as fornecedor, pago, nomeempresa as unidade, produ as descricao
            FROM despesas_gerais
            WHERE ano = :ano AND (nomefor LIKE :search OR produ LIKE :search OR nomeempresa LIKE :search)
            ORDER BY CAST(NULLIF(REPLACE(pago, ',', '.'), '') AS FLOAT) DESC
            LIMIT :lim
        """)
        params = {"ano": year, "search": f"%{query}%", "lim": limit}
    else:
        sql = text("""
            SELECT datae as data, nomefor as fornecedor, pago, nomeempresa as unidade, produ as descricao
            FROM despesas_gerais
            WHERE ano = :ano
            ORDER BY CAST(NULLIF(REPLACE(pago, ',', '.'), '') AS FLOAT) DESC
            LIMIT :lim
        """)
        params = {"ano": year, "lim": limit}

    df = pd.read_sql_query(sql, conn, params=params)
    if df.empty:
        return pd.DataFrame(columns=["data", "fornecedor", "pago", "unidade", "descricao"])

    df["pago"] = pd.to_numeric(df["pago"].str.replace(",", "."), errors="coerce").fillna(0)
    return df
