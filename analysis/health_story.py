import sqlite3
from datetime import date

import pandas as pd

from analysis.contract_anomalies import NEAR_THRESHOLD_PCT, THRESHOLD

DISPENSATION_THRESHOLD = 57_000
SAUDE_EMPRESA = "2"


def _to_float(series: pd.Series) -> pd.Series:
    return pd.to_numeric(series.astype(str).str.replace(",", "."), errors="coerce").fillna(0)


def _emendas(conn: sqlite3.Connection, year: int, empresa_id: str) -> tuple[pd.DataFrame, float]:
    df = pd.read_sql_query(
        """SELECT numero_emenda, resumo, valor_total, empenhado, autor,
                  tipo_emenda_descr, esfera_origem, ato_normativo, destinacao_descr
           FROM emendas_cad WHERE ano = ? AND empresa = ?""",
        conn,
        params=(year, empresa_id),
    )
    if df.empty:
        return df, 0.0

    # Rename for consistency with expected output
    df = df.rename(
        columns={
            "numero_emenda": "numero",
            "resumo": "descricao",
            "valor_total": "valor",
            "tipo_emenda_descr": "Tipo da Emenda",
            "esfera_origem": "Esfera de Origem",
            "ato_normativo": "ato_normativo",
            "destinacao_descr": "Destinação",
        }
    )

    df["valor"] = _to_float(df["valor"])
    df["empenhado"] = _to_float(df["empenhado"]).replace(0, pd.NA)
    return df, float(df["valor"].sum())


def _budget(conn: sqlite3.Connection, year: int, empresa_id: str) -> dict:
    df = pd.read_sql_query(
        "SELECT empenhado, dotacao_atualizada FROM despesas_por_orgao WHERE ano = ? AND empresa = ?",
        conn,
        params=(year, empresa_id),
    )
    dotacao = _to_float(df["dotacao_atualizada"]).sum()
    empenhado = _to_float(df["empenhado"]).sum()
    taxa = empenhado / dotacao if dotacao > 0 else 0.0
    flag = taxa < 0.70 and year < date.today().year
    return {"dotacao": dotacao, "empenhado": empenhado, "taxa_execucao": taxa, "flag_under_execution": flag}


def _execution_trend(conn: sqlite3.Connection, empresa_id: str) -> pd.DataFrame:
    df = pd.read_sql_query(
        "SELECT ano, empenhado FROM despesas_por_orgao WHERE empresa = ?",
        conn,
        params=(empresa_id,),
    )
    df["empenhado"] = _to_float(df["empenhado"])
    return df.groupby("ano", as_index=False)["empenhado"].sum().sort_values("ano").reset_index(drop=True)


def _execution_flow(conn: sqlite3.Connection, year: int, empresa_id: str) -> pd.DataFrame:
    df = pd.read_sql_query(
        "SELECT empenhado, liquidado, pago FROM despesas_por_orgao WHERE ano = ? AND empresa = ?",
        conn,
        params=(year, empresa_id),
    )
    df["empenhado"] = _to_float(df["empenhado"])
    df["liquidado"] = _to_float(df["liquidado"])
    df["pago"] = _to_float(df["pago"])
    return pd.DataFrame(
        {
            "Categoria": ["Empenhado", "Liquidado", "Pago"],
            "Valor (R$)": [df["empenhado"].sum(), df["liquidado"].sum(), df["pago"].sum()],
        }
    )


def _contracts_by_modality(conn: sqlite3.Connection, year: int, empresa_id: str) -> pd.DataFrame:
    df = pd.read_sql_query(
        "SELECT modali, valcon FROM contratos WHERE ano = ? AND empresa = ?",
        conn,
        params=(year, empresa_id),
    )
    if df.empty:
        return pd.DataFrame(columns=["modality", "count", "total_value"])
    df["valor_num"] = _to_float(df["valcon"])
    df["modality"] = df["modali"].fillna("").str.strip()
    df["modality"] = df["modality"].where(df["modality"] != "", "Sem Informação")
    return (
        df.groupby("modality")
        .agg(count=("modality", "size"), total_value=("valor_num", "sum"))
        .reset_index()
        .sort_values("total_value", ascending=False)
    )


def _adesao_de_ata(conn: sqlite3.Connection, year: int, empresa_id: str) -> tuple[pd.DataFrame, float]:
    # Fetch all Carona licitacoes and sum the value of any linked contracts
    query = """
        SELECT
            l.numero,
            l.discr as objeto,
            l.valor as licitacao_valor,
            SUM(c.valcon) as total_c_valor,
            SUM(c.empenhado) as total_c_empenhado
        FROM licitacoes l
        LEFT JOIN contratos c
            ON c.licitacao_numero = l.numero
            AND c.ano = l.ano
            AND c.empresa = l.empresa
        WHERE l.ano = ? AND l.empresa = ? AND l.carona = 'S'
        GROUP BY l.numero
    """
    try:
        df = pd.read_sql_query(query, conn, params=(year, empresa_id))
        total_value = float(_to_float(df["total_c_valor"]).sum()) if not df.empty else 0.0
        # Add a column indicating if a contract is attached (has total_c_valor > 0)
        df["has_contract"] = df["total_c_valor"] > 0
        return df, total_value
    except Exception:
        return pd.DataFrame(), 0.0


def _bidding_gaps(conn: sqlite3.Connection, year: int, empresa_id: str) -> pd.DataFrame:
    df = pd.read_sql_query(
        "SELECT numero, fornecedor, objeto, valcon, licitacao_numero, modali FROM contratos WHERE ano = ? AND empresa = ?",
        conn,
        params=(year, empresa_id),
    )
    df = df[df["licitacao_numero"].fillna("").str.strip() == ""].copy()
    df["valor_num"] = _to_float(df["valcon"])
    return df[df["valor_num"] > DISPENSATION_THRESHOLD].drop(columns=["valor_num", "licitacao_numero"])


def _top_suppliers(conn: sqlite3.Connection, year: int, empresa_id: str) -> tuple[pd.DataFrame, float]:
    df = pd.read_sql_query(
        "SELECT codigo, descricao, empenhado FROM despesas_por_fornecedor WHERE ano = ? AND empresa = ?",
        conn,
        params=(year, empresa_id),
    )
    df["empenhado"] = _to_float(df["empenhado"])
    df = df.groupby(["codigo", "descricao"], as_index=False)["empenhado"].sum()
    total = df["empenhado"].sum()
    df["percentual"] = df["empenhado"] / total * 100 if total > 0 else 0
    top10 = df.nlargest(10, "empenhado").reset_index(drop=True)
    shares = df["empenhado"] / total if total > 0 else df["empenhado"] * 0
    hhi = float((shares**2).sum() * 10000)
    return top10, hhi


def _splitting(conn: sqlite3.Connection, year: int, empresa_id: str) -> pd.DataFrame:
    df = pd.read_sql_query(
        "SELECT fornecedor, valcon, objeto FROM contratos WHERE ano = ? AND empresa = ?",
        conn,
        params=(year, empresa_id),
    )
    df["valor_num"] = _to_float(df["valcon"])
    lower = THRESHOLD * (1 - NEAR_THRESHOLD_PCT)
    near = df[(df["valor_num"] >= lower) & (df["valor_num"] < THRESHOLD)]
    counts = near.groupby("fornecedor").size()
    return near[near["fornecedor"].isin(counts[counts >= 3].index)].copy()


def _transfers_to_health(conn: sqlite3.Connection, year: int, empresa_id: str) -> tuple[pd.DataFrame, float]:
    # Transfers only apply to the health fund (empresa '2'); other funds receive from different sources.
    if empresa_id != SAUDE_EMPRESA:
        return pd.DataFrame(), 0.0
    df = pd.read_sql_query(
        "SELECT mes, entidade_pagadora, entidade_recebedora, repasse, devolucao FROM transferencias "
        "WHERE empresa = '7' AND ano = ? AND UPPER(entidade_recebedora) LIKE '%SAUDE%'",
        conn,
        params=(year,),
    )
    if df.empty:
        return df, 0.0
    df["repasse_num"] = _to_float(df["repasse"])
    df["devolucao_num"] = _to_float(df["devolucao"])
    total = float((df["repasse_num"] - df["devolucao_num"]).sum())
    return df, total


def _top_suppliers_services(conn: sqlite3.Connection, year: int, empresa_id: str) -> pd.DataFrame:
    query = """
        SELECT fornecedor, objeto, SUM(valcon) as total
        FROM contratos
        WHERE ano = ? AND empresa = ?
        GROUP BY fornecedor, objeto
        ORDER BY total DESC
    """
    df = pd.read_sql_query(query, conn, params=(year, empresa_id))
    df["total"] = _to_float(df["total"])
    return df


def run(conn: sqlite3.Connection, year: int, empresa_id: str = SAUDE_EMPRESA) -> dict:
    emendas_df, emendas_total = _emendas(conn, year, empresa_id)
    budget = _budget(conn, year, empresa_id)
    execution_trend = _execution_trend(conn, empresa_id)
    execution_flow = _execution_flow(conn, year, empresa_id)
    contracts_by_modality = _contracts_by_modality(conn, year, empresa_id)
    adesao_df, adesao_value = _adesao_de_ata(conn, year, empresa_id)
    bidding_gaps = _bidding_gaps(conn, year, empresa_id)
    top_suppliers, hhi = _top_suppliers(conn, year, empresa_id)
    top_suppliers_services = _top_suppliers_services(conn, year, empresa_id)
    splitting = _splitting(conn, year, empresa_id)
    transfers_df, transfers_total = _transfers_to_health(conn, year, empresa_id)
    return {
        "emendas": emendas_df,
        "emendas_total": emendas_total,
        "budget": budget,
        "execution_trend": execution_trend,
        "execution_flow": execution_flow,
        "contracts_by_modality": contracts_by_modality,
        "adesao_de_ata_list": adesao_df,
        "adesao_de_ata_count": len(adesao_df),
        "adesao_de_ata_value": adesao_value,
        "bidding_gaps": bidding_gaps,
        "top_suppliers": top_suppliers,
        "top_suppliers_services": top_suppliers_services,
        "hhi": hhi,
        "splitting": splitting,
        "transfers_to_health": transfers_df,
        "transfers_to_health_total": transfers_total,
    }
