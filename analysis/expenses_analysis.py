import unicodedata
from typing import Any

import pandas as pd
from sqlalchemy import bindparam, text

from dashboard.shared import CIDADE_CLEAN

# Payroll disbursed through department heads — not individual suppliers
# Covers: "E OUTROS", "E OUTRO", "E OUT.", "e OUTROS", etc.

SUBVENCOES_SOCIAIS_NATUREZA = "43"
FORNECEDORES_NATUREZA_MAP = {
    "30": "30 - Material de Consumo",
    "36": "36 - Serv. Terceiros (Pessoa Física)",
    "39": "39 - Serv. Terceiros (Pessoa Jurídica)",
    "52": "52 - Equipamentos e Mat. Permanente",
}
DESPESAS_MAP = {
    **FORNECEDORES_NATUREZA_MAP,
    SUBVENCOES_SOCIAIS_NATUREZA: "43 - Subvenções Sociais",
    # TODO: adicionar outros elementos de despesa conforme necessário
}


def get_elemento_label(elemento: str) -> str:
    """Retorna o label descritivo para o elemento da despesa."""
    return DESPESAS_MAP.get(str(elemento), f"Elemento {elemento}")


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
    """
    Retorna um DataFrame detalhado dos principais fornecedores, incluindo informações sobre empenhado, liquidado e pago.
    """
    # JOIN para buscar o elemento de despesa associado
    # Filtro estrito: apenas elementos de FORNECEDORES_NATUREZA_MAP e fornecedores que nao tenham natureza '43' (Subvenções Sociais).
    sql = text(
        """
        SELECT
            f.descricao as fornecedor,
            f.insmf,
            f.cepci as cidade,
            f.codigo,
            f.empenhado,
            f.liquidado,
            f.pago,
            MAX(g.produ) as descricao,
            MAX(g.elemento) as elemento
        FROM despesas_por_fornecedor f
        LEFT JOIN despesas_gerais g
          ON f.ano = g.ano
          AND f.descricao = g.nomefor
        WHERE f.ano = :ano
        AND g.elemento IN :elementos
        GROUP BY f.descricao, f.insmf, f.cepci, f.codigo, f.empenhado, f.liquidado, f.pago
        """
    ).bindparams(
        bindparam("elementos", expanding=True, value=list(FORNECEDORES_NATUREZA_MAP.keys())),
    )

    df = pd.read_sql_query(
        sql,
        conn,
        params={
            "ano": year,
            "subvencoes_sociais": SUBVENCOES_SOCIAIS_NATUREZA,
        },
    )

    if df.empty:
        return pd.DataFrame(
            columns=[
                "fornecedor",
                "insmf",
                "cidade",
                "codigo",
                "elemento",
                "empenhado",
                "liquidado",
                "pago",
                "descricao",
            ]
        )

    df["empenhado"] = pd.to_numeric(df["empenhado"].str.replace(",", "."), errors="coerce").fillna(0)
    df["liquidado"] = pd.to_numeric(df["liquidado"].str.replace(",", "."), errors="coerce").fillna(0)
    df["pago"] = pd.to_numeric(df["pago"].str.replace(",", "."), errors="coerce").fillna(0)

    return (
        df.groupby(["fornecedor", "insmf", "cidade", "codigo", "elemento"], as_index=False)[
            ["empenhado", "liquidado", "pago", "descricao"]
        ]
        .sum()
        .sort_values("pago", ascending=False)
    )


def get_local_spending_impact(conn: Any, year: int) -> dict:
    sql = text(
        """
        SELECT f.cepci as cidade, f.pago
        FROM despesas_por_fornecedor f
        LEFT JOIN despesas_gerais g
          ON f.ano = g.ano
          AND f.descricao = g.nomefor
        WHERE f.ano = :ano
        AND g.elemento IN :elementos
        """
    ).bindparams(
        bindparam("elementos", expanding=True, value=list(FORNECEDORES_NATUREZA_MAP.keys())),
    )

    df = pd.read_sql_query(sql, conn, params={"ano": year})
    if df.empty:
        return {"local_pago": 0.0, "externo_pago": 0.0, "total_pago": 0.0, "pct_local": 0.0}

    df["pago"] = pd.to_numeric(df["pago"].str.replace(",", "."), errors="coerce").fillna(0)
    df["cidade_clean"] = (
        df["cidade"]
        .fillna("")
        .astype(str)
        .str.strip()
        .str.upper()
        .apply(lambda x: unicodedata.normalize("NFD", x).encode("ascii", "ignore").decode("ascii"))
    )

    is_local = df["cidade_clean"] == CIDADE_CLEAN
    local_pago = df[is_local]["pago"].sum()
    externo_pago = df[~is_local]["pago"].sum()
    total_pago = local_pago + externo_pago

    return {
        "local_pago": float(local_pago),
        "externo_pago": float(externo_pago),
        "total_pago": float(total_pago),
        "pct_local": (local_pago / total_pago * 100) if total_pago > 0 else 0.0,
    }


def get_spending_by_city(conn: Any, year: int, top_n: int = 5) -> pd.DataFrame:
    sql = text(
        """
        SELECT f.cepci as cidade, f.pago
        FROM despesas_por_fornecedor f
        LEFT JOIN despesas_gerais g
          ON f.ano = g.ano
          AND f.descricao = g.nomefor
        WHERE f.ano = :ano
        AND g.elemento IN :elementos
        """
    ).bindparams(
        bindparam("elementos", expanding=True, value=list(FORNECEDORES_NATUREZA_MAP.keys())),
    )

    df = pd.read_sql_query(sql, conn, params={"ano": year})
    if df.empty:
        return pd.DataFrame(columns=["cidade", "pago"])

    df["pago"] = pd.to_numeric(df["pago"].astype(str).str.replace(",", "."), errors="coerce").fillna(0)
    df["cidade_clean"] = (
        df["cidade"]
        .fillna("")
        .astype(str)
        .str.strip()
        .str.upper()
        .apply(lambda x: unicodedata.normalize("NFD", x).encode("ascii", "ignore").decode("ascii"))
    )
    df["cidade_label"] = df["cidade"].fillna("").astype(str).str.strip().str.title()
    # treat blank or numeric-only values as unknown
    df.loc[df["cidade_label"].str.fullmatch(r"\d*"), "cidade_label"] = "Não Informado"
    df.loc[df["cidade_clean"] == CIDADE_CLEAN, "cidade_label"] = "Negócios Locais (Porciúncula)"

    by_city = df.groupby("cidade_label", as_index=False)["pago"].sum().sort_values("pago", ascending=False)  # type: ignore

    local_row = by_city[by_city["cidade_label"] == "Negócios Locais (Porciúncula)"].copy()
    external = by_city[by_city["cidade_label"] != "Negócios Locais (Porciúncula)"].copy()

    unknown = external[external["cidade_label"] == "Não Informado"]
    ranked = external[external["cidade_label"] != "Não Informado"].sort_values("pago", ascending=False)

    top = ranked.head(top_n).copy()
    outros_pago = ranked.iloc[top_n:]["pago"].sum() + unknown["pago"].sum()

    rows = [local_row] if not local_row.empty else []
    rows.append(top)
    if outros_pago > 0:
        rows.append(pd.DataFrame([{"cidade_label": "Outros (incluindo Não Informado)", "pago": outros_pago}]))

    result = pd.concat(rows, ignore_index=True)
    result = result.rename(columns={"cidade_label": "cidade"})
    return result


def get_departmental_payroll(conn: Any, year: int) -> pd.DataFrame:
    df = pd.read_sql_query(
        text(
            "SELECT descricao, pago FROM despesas_por_fornecedor WHERE ano = :ano AND descricao ~* ' E OUT(ROS?|\\.)'"
        ),
        conn,
        params={"ano": year},
    )
    if df.empty:
        return pd.DataFrame(columns=["descricao", "pago"])

    df["pago"] = pd.to_numeric(df["pago"].str.replace(",", "."), errors="coerce").fillna(0)
    return df.groupby("descricao", as_index=False)["pago"].sum().sort_values("pago", ascending=False)  # type: ignore


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
            WHERE ano = :ano AND (nomefor ILIKE :search OR produ ILIKE :search OR nomeempresa ILIKE :search)
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
    df["data"] = pd.to_datetime(df["data"], dayfirst=True, errors="coerce").dt.date
    return df


def get_searchable_diarias(conn: Any, year: int, query: str, limit: int = 150) -> pd.DataFrame:
    if query.strip():
        sql = text("""
            SELECT data, favorecido as servidor, cargo, valor, unidade, descricao as historico
            FROM diarias
            WHERE ano = :ano AND (favorecido ILIKE :search OR unidade ILIKE :search OR cargo ILIKE :search)
            ORDER BY data DESC
        """)
        params = {"ano": year, "search": f"%{query}%"}
    else:
        sql = text("""
            SELECT data, favorecido as servidor, cargo, valor, unidade, descricao as historico
            FROM diarias
            WHERE ano = :ano
            ORDER BY data DESC LIMIT :lim
        """)
        params = {"ano": year, "lim": limit}

    df = pd.read_sql_query(sql, conn, params=params)
    if df.empty:
        return pd.DataFrame(columns=["data", "servidor", "cargo", "valor", "unidade", "historico"])
    df["valor"] = pd.to_numeric(df["valor"].str.replace(",", "."), errors="coerce").fillna(0)
    return df


def departmental_payroll_total(df: pd.DataFrame) -> float:
    """Return total pago distributed via departmental payroll responsibles."""
    return float(df["pago"].sum()) if not df.empty else 0.0
