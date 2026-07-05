from typing import Any

import pandas as pd
from sqlalchemy import text

from analysis.constants import NEAR_THRESHOLD_PCT, dispensation_threshold


def contagens_fracionamento_por_ano(conn: Any, years: list[int]) -> dict[int, int]:
    placeholders = ", ".join(str(y) for y in years)
    df = pd.read_sql_query(
        text(
            f"SELECT ano, empresa, fornecedor, valcon, numobra, tipocoobra, objeto"
            f" FROM contratos WHERE ano IN ({placeholders})"
        ),
        conn,
    )
    df["valor_num"] = pd.to_numeric(df["valcon"].astype(str).str.replace(",", "."), errors="coerce").fillna(0)
    df["limite"] = df.apply(
        lambda r: dispensation_threshold(r.get("numobra"), r.get("tipocoobra"), r.get("objeto")), axis=1
    )
    df["limite_inferior"] = df["limite"] * (1 - NEAR_THRESHOLD_PCT)
    df["proximo_limite"] = (df["valor_num"] >= df["limite_inferior"]) & (df["valor_num"] < df["limite"])

    result = {}
    for y in years:
        proximo_ano = df[(df["ano"] == y) & df["proximo_limite"]]
        # Agrupa por órgão executor + fornecedor (subelemento de despesa não disponível na tabela contratos)
        counts = proximo_ano.groupby(["empresa", "fornecedor"]).size()
        result[y] = int((counts >= 3).sum())
    return result


def run(conn: Any, year: int) -> dict:
    contratos = pd.read_sql_query(
        text(
            "SELECT ano, empresa, numero, fornecedor, objeto, valcon, licitacao_numero, mes,"
            " numobra, tipocoobra"
            " FROM contratos WHERE ano = :ano"
        ),
        conn,
        params={"ano": year},
    )
    contratos["valor_num"] = pd.to_numeric(
        contratos["valcon"].astype(str).str.replace(",", "."), errors="coerce"
    ).fillna(0)
    contratos["limite"] = contratos.apply(
        lambda r: dispensation_threshold(r.get("numobra"), r.get("tipocoobra"), r.get("objeto")), axis=1
    )
    contratos["limite_inferior"] = contratos["limite"] * (1 - NEAR_THRESHOLD_PCT)
    proximo = contratos[
        (contratos["valor_num"] >= contratos["limite_inferior"]) & (contratos["valor_num"] < contratos["limite"])
    ]

    # Fracionamento: mesmo órgão executor + mesmo fornecedor com 3+ contratos abaixo do limite aplicável
    # (subelemento de despesa refinaria ainda mais, mas não está disponível na tabela contratos)
    contagem_fornecedores = proximo.groupby(["empresa", "fornecedor"]).size()
    chaves_fracionamento = contagem_fornecedores[contagem_fornecedores >= 3].index
    fracionamento = proximo[proximo.set_index(["empresa", "fornecedor"]).index.isin(chaves_fracionamento)].copy()
    if not fracionamento.empty:
        fracionamento["Período"] = (
            fracionamento["mes"].astype(str).str.zfill(2) + "/" + fracionamento["ano"].astype(str)
        )

    totais_orgao = contratos.groupby("empresa").size().rename("total")
    orgao_fornecedor = contratos.groupby(["empresa", "fornecedor"]).size().rename("quantidade").reset_index()
    orgao_fornecedor = orgao_fornecedor.join(totais_orgao, on="empresa")
    orgao_fornecedor["pct"] = orgao_fornecedor["quantidade"] / orgao_fornecedor["total"]
    fornecedor_recorrente = orgao_fornecedor[orgao_fornecedor["pct"] > 0.5].copy()

    licitacoes = pd.read_sql_query(
        text("SELECT numero, modalidade, objeto, data_abertura FROM licitacoes WHERE ano = :ano"),
        conn,
        params={"ano": year},
    )
    janela_curta = pd.DataFrame()
    if not licitacoes.empty and "data_abertura" in licitacoes.columns:
        licitacoes["data_abertura"] = pd.to_datetime(licitacoes["data_abertura"], errors="coerce")
        licitacoes = licitacoes.sort_values("data_abertura")
        licitacoes["dias_desde_anterior"] = licitacoes["data_abertura"].diff().dt.days
        janela_curta = licitacoes[licitacoes["dias_desde_anterior"] < 5].copy()

    return {
        "fracionamento": fracionamento,
        "fornecedor_recorrente": fornecedor_recorrente,
        "janela_curta": janela_curta,
    }
