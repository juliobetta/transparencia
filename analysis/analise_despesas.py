import unicodedata
from typing import Any

import pandas as pd
import streamlit as st
from sqlalchemy import bindparam, text
from sqlalchemy.engine import Engine

from analysis.constants import (
    DESPESAS_MAP,
    ELEMENTO_FOLHA_PESSOAL,
    ELEMENTO_SUBVENCOES_SOCIAIS,
    FORNECEDORES_NATUREZA_MAP,
)
from dashboard.shared import CIDADE_CLEAN

_hash: dict[str | type[Any], Any] = {Engine: lambda e: str(e.url)}

# Folha de pessoal distribuída via responsáveis de unidade — não por fornecedores individuais


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


def get_metricas_gerais_despesas(conn: Any, year: int) -> dict:
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


def get_despesas_por_unidade(conn: Any, year: int) -> pd.DataFrame:
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


def get_principais_fornecedores_detalhados(conn: Any, year: int) -> pd.DataFrame:
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
            "subvencoes_sociais": ELEMENTO_SUBVENCOES_SOCIAIS,
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


def get_impacto_gastos_locais(conn: Any, year: int) -> dict:
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


def get_gastos_por_municipio(conn: Any, year: int, top_n: int = 5) -> pd.DataFrame:
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


def get_folha_por_orgao(conn: Any, year: int) -> pd.DataFrame:
    # Filtra folha de pessoal (elemento 11) diretamente da despesas_gerais
    query = text("""
        SELECT nomefor as descricao, SUM(CAST(NULLIF(REPLACE(pago, ',', '.'), '') AS FLOAT)) as pago
        FROM despesas_gerais
        WHERE ano = :ano AND elemento = :elemento
        GROUP BY nomefor
    """)
    df = pd.read_sql_query(query, conn, params={"ano": year, "elemento": ELEMENTO_FOLHA_PESSOAL})
    if df.empty:
        return pd.DataFrame(columns=["descricao", "pago"])

    return df.groupby("descricao", as_index=False)["pago"].sum().sort_values("pago", ascending=False)


def get_resumo_diarias(conn: Any, year: int) -> dict:
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


def get_principais_beneficiarios_diarias(conn: Any, year: int) -> pd.DataFrame:
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


def get_transacoes_pesquisaveis(conn: Any, year: int, query: str, limit: int = 500) -> pd.DataFrame:
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


def get_diarias_pesquisaveis(conn: Any, year: int, query: str, limit: int = 150) -> pd.DataFrame:
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


def total_folha_por_orgao(df: pd.DataFrame) -> float:
    return float(df["pago"].sum()) if not df.empty else 0.0


@st.cache_data(hash_funcs=_hash, show_spinner=False)
def get_analise_intensidade_pessoal(_conn: Any, year: int) -> pd.DataFrame:
    """
    Retorna a análise da intensidade de gastos com pessoal por órgão.

    Compara os gastos totais de cada órgão com os gastos específicos de folha de pessoal,
    calculando a porcentagem que a folha representa no orçamento total de cada órgão.
    """
    df_total = get_despesas_por_unidade(_conn, year)
    df_folha = get_folha_por_orgao(_conn, year)

    df = df_total.merge(df_folha, on="descricao", how="left", suffixes=("", "_folha"))
    df = df.rename(
        columns={
            "descricao": "orgao",
            "pago": "gasto_total",
            "pago_folha": "gasto_folha",
        }
    )
    df["gasto_folha"] = df["gasto_folha"].fillna(0)
    df["pct_folha"] = (df["gasto_folha"] / df["gasto_total"] * 100).fillna(0)

    return df[["orgao", "gasto_total", "gasto_folha", "pct_folha"]]


def get_metricas_por_ano(conn: Any, years: list[int]) -> dict[int, dict]:
    return {year: get_metricas_gerais_despesas(conn, year) for year in years}


def get_impacto_por_ano(conn: Any, years: list[int]) -> dict[int, dict]:
    return {year: get_impacto_gastos_locais(conn, year) for year in years}


def get_resumo_diarias_por_ano(conn: Any, years: list[int]) -> dict[int, dict]:
    return {year: get_resumo_diarias(conn, year) for year in years}


def total_folha_orgao_por_ano(conn: Any, years: list[int]) -> dict[int, float]:
    return {year: total_folha_por_orgao(get_folha_por_orgao(conn, year)) for year in years}


@st.cache_data(hash_funcs=_hash, show_spinner=False)
def get_perfil_cargos_confianca(_conn: Any, years: list[int]) -> pd.DataFrame:
    """
    Retorna o perfil dos cargos de confiança da prefeitura categorizados por vínculo e categoria funcional.
    """
    query = text("""
        SELECT
            ano,
            CASE
                WHEN LOWER(categoriafuncional) LIKE '%inativo%' OR LOWER(categoriafuncional) LIKE '%pensionista%' OR LOWER(vinculo) LIKE '%inativo%' OR LOWER(vinculo) LIKE '%pensionista%' THEN 'Inativos e Pensionistas'
                WHEN LOWER(cargo) LIKE '%conselheiro%' OR LOWER(categoriafuncional) LIKE '%cedido%' OR LOWER(vinculo) LIKE '%cedido%' OR LOWER(vinculo) IN ('macaeprev', 'macaeprev i', 'funprev', 'funprev active', 'rppsi', 'rpps active') THEN 'Conselhos e Cedidos Externos'
                WHEN vinculo LIKE '%FG%' THEN 'Servidor Efetivo com Função de Confiança (DAI/FG)'
                WHEN vinculo LIKE '%CC%' OR categoriafuncional = 'Efetivos ocupantes de cargo comissionado' THEN 'Servidor Efetivo com Cargo Comissionado (DAS/CC)'
                WHEN categoriafuncional = 'Cargo comissionado extra-quadro' OR vinculo = 'Comissionado INSS' OR LOWER(vinculo) LIKE 'cargo comissionado%' THEN 'Comissionado Externo (DAS/CC - Sem Vínculo)'
                WHEN formaprovimento = 'CONCURSO PUBLICO' OR categoriafuncional = 'Efetivos' THEN 'Servidor Efetivo de Carreira'
                WHEN formaprovimento = 'TEMPO DETERMINADO' OR categoriafuncional LIKE '%interesse público%' THEN 'Contrato Temporário'
                WHEN categoriafuncional = 'Eletivos' OR LOWER(cargo) LIKE '%prefeito%' OR LOWER(cargo) LIKE '%vereador%' OR LOWER(cargo) LIKE '%secretario%' OR LOWER(vinculo) LIKE '%politico%' THEN 'Agente Político (Eletivo/Secretário)'
                ELSE 'Outros'
            END as tipo_vinculo_detalhado,
            COUNT(*) as quantidade,
            SUM(CAST(NULLIF(REPLACE(REPLACE(proventos, '.', ''), ',', '.'), '') AS FLOAT)) as total_gasto
        FROM pessoal
        WHERE ano IN :anos
        GROUP BY ano, tipo_vinculo_detalhado
    """)
    df = pd.read_sql_query(query, _conn, params={"anos": tuple(years)})

    if df.empty:
        return pd.DataFrame(columns=["ano", "tipo_vinculo_detalhado", "quantidade", "total_gasto"])

    return df
