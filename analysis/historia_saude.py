import unicodedata
from datetime import date
from typing import Any

import pandas as pd
from sqlalchemy import bindparam, text

from analysis.constants import FORNECEDORES_NATUREZA_MAP, NEAR_THRESHOLD_PCT, dispensation_threshold

SAUDE_EMPRESA = "2"


def _to_float(series: pd.Series) -> pd.Series:
    return pd.to_numeric(series.astype(str).str.replace(",", "."), errors="coerce").fillna(0)


def _emendas(conn: Any, year: int, empresa_id: str) -> tuple[pd.DataFrame, float]:
    df = pd.read_sql_query(
        text("""SELECT numero_emenda, resumo, valor_total, empenhado, autor,
                  tipo_emenda_descr, esfera_origem, ato_normativo, destinacao_descr
           FROM emendas_cad WHERE ano = :ano AND empresa = :empresa"""),
        conn,
        params={"ano": year, "empresa": empresa_id},
    )
    if df.empty:
        return df, 0.0

    df = df.rename(
        columns={
            "numero_emenda": "Nº",
            "resumo": "Objeto",
            "valor_total": "Valor Autorizado",
            "empenhado": "Empenhado",
            "autor": "Autor",
            "tipo_emenda_descr": "Tipo da Emenda",
            "esfera_origem": "Esfera de Origem",
            "ato_normativo": "Ato Normativo",
            "destinacao_descr": "Destinação",
        }
    )

    df["Valor Autorizado"] = _to_float(df["Valor Autorizado"])
    df["Empenhado"] = _to_float(df["Empenhado"]).replace(0, pd.NA)
    return df, float(df["Valor Autorizado"].sum())


def _budget(conn: Any, year: int, empresa_id: str) -> dict:
    df = pd.read_sql_query(
        text("SELECT empenhado, dotacao_atualizada FROM despesas_por_orgao WHERE ano = :ano AND empresa = :empresa"),
        conn,
        params={"ano": year, "empresa": empresa_id},
    )
    dotacao = _to_float(df["dotacao_atualizada"]).sum()
    empenhado = _to_float(df["empenhado"]).sum()
    taxa = empenhado / dotacao if dotacao > 0 else 0.0
    flag = taxa < 0.70 and year < date.today().year
    return {"dotacao": dotacao, "empenhado": empenhado, "taxa_execucao": taxa, "alerta_sub_execucao": flag}


def _execution_trend(conn: Any, empresa_id: str) -> pd.DataFrame:
    df = pd.read_sql_query(
        text("SELECT ano, empenhado FROM despesas_por_orgao WHERE empresa = :empresa"),
        conn,
        params={"empresa": empresa_id},
    )
    df["empenhado"] = _to_float(df["empenhado"])
    return df.groupby("ano", as_index=False)["empenhado"].sum().sort_values("ano").reset_index(drop=True)


def _execution_flow(conn: Any, year: int, empresa_id: str) -> pd.DataFrame:
    df = pd.read_sql_query(
        text("SELECT empenhado, liquidado, pago FROM despesas_por_orgao WHERE ano = :ano AND empresa = :empresa"),
        conn,
        params={"ano": year, "empresa": empresa_id},
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


def _contracts_by_modality(conn: Any, year: int, empresa_id: str) -> pd.DataFrame:
    df = pd.read_sql_query(
        text("SELECT modali, valcon, mes FROM contratos WHERE ano = :ano AND empresa = :empresa"),
        conn,
        params={"ano": year, "empresa": empresa_id},
    )
    if df.empty:
        return pd.DataFrame(columns=["modalidade", "quantidade", "valor_total", "periodo"])
    df["valor_num"] = _to_float(df["valcon"])
    df["modalidade"] = df["modali"].fillna("").str.strip()
    df["modalidade"] = df["modalidade"].where(df["modalidade"] != "", "Sem Informação")
    df["periodo"] = df["mes"].astype(str).str.zfill(2) + "/" + str(year)
    return (
        df.groupby(["modalidade", "periodo"])
        .agg(quantidade=("modalidade", "size"), valor_total=("valor_num", "sum"))
        .reset_index()
        .sort_values("valor_total", ascending=False)
    )


def _adesao_de_ata(conn: Any, year: int, empresa_id: str) -> tuple[pd.DataFrame, float]:
    query = text("""
        SELECT
            l.numero,
            l.discr as objeto,
            l.valor as licitacao_valor,
            SUM(CAST(NULLIF(REPLACE(c.valcon, ',', '.'), '') AS FLOAT)) as total_c_valor,
            SUM(CAST(NULLIF(REPLACE(c.empenhado, ',', '.'), '') AS FLOAT)) as total_c_empenhado
        FROM licitacoes l
        LEFT JOIN contratos c
            ON c.licitacao_numero = l.numero
            AND c.ano = l.ano
            AND c.empresa = l.empresa
        WHERE l.ano = :ano AND l.empresa = :empresa AND l.carona = 'S'
        GROUP BY l.numero, l.discr, l.valor
    """)
    try:
        df = pd.read_sql_query(query, conn, params={"ano": year, "empresa": empresa_id})
        total_value = float(_to_float(df["total_c_valor"]).sum()) if not df.empty else 0.0
        df["tem_contrato"] = df["total_c_valor"] > 0
        return df, total_value
    except Exception:
        return pd.DataFrame(), 0.0


def _licitacao_gaps(conn: Any, year: int, empresa_id: str) -> pd.DataFrame:
    df = pd.read_sql_query(
        text(
            "SELECT ano, numero, fornecedor, objeto, valcon, licitacao_numero, modali, mes,"
            " numobra, tipocoobra, fundlegal"
            " FROM contratos WHERE ano = :ano AND empresa = :empresa"
        ),
        conn,
        params={"ano": year, "empresa": empresa_id},
    )
    df = df[df["licitacao_numero"].fillna("").str.strip() == ""].copy()
    df["valor_num"] = _to_float(df["valcon"])
    df["limite"] = df.apply(
        lambda r: dispensation_threshold(r.get("numobra"), r.get("tipocoobra"), r.get("objeto")), axis=1
    )
    result = df[df["valor_num"] > df["limite"]].drop(columns=["valor_num", "limite", "licitacao_numero"])

    # Classifica contratos isentos de licitação pela lei, independente do valor, com base em colunas estruturadas:
    #   - MODALI ou FUNDLEGAL contendo INEXIGIBILIDADE ou DISPENSA
    #   - Fornecedor contendo CONSORCIO
    #   - Objeto contendo RATEIO ou CONTRATO DE PROGRAMA

    def _ascii(s: pd.Series) -> pd.Series:
        return s.fillna("").apply(
            lambda v: unicodedata.normalize("NFD", str(v)).encode("ascii", "ignore").decode("ascii").lower()
        )

    modali_norm = _ascii(result["modali"])
    fundlegal_norm = _ascii(result["fundlegal"])
    fornecedor_norm = _ascii(result["fornecedor"])
    objeto_norm = _ascii(result["objeto"])
    result["isento_legalmente"] = (
        modali_norm.str.contains("inexig", na=False)
        | fundlegal_norm.str.contains("inexig", na=False)
        | fornecedor_norm.str.contains("consorcio", na=False)
        | objeto_norm.str.contains("rateio", na=False)
        | objeto_norm.str.contains("cont. programa", na=False)
        | objeto_norm.str.contains("contrato de programa", na=False)
    )
    return result


def _splitting(conn: Any, year: int, empresa_id: str) -> pd.DataFrame:
    df = pd.read_sql_query(
        text(
            "SELECT ano, fornecedor, valcon, objeto, mes, numobra, tipocoobra"
            " FROM contratos WHERE ano = :ano AND empresa = :empresa"
        ),
        conn,
        params={"ano": year, "empresa": empresa_id},
    )
    df["valor_num"] = _to_float(df["valcon"])
    df["limite"] = df.apply(
        lambda r: dispensation_threshold(r.get("numobra"), r.get("tipocoobra"), r.get("objeto")), axis=1
    )
    df["limite_inferior"] = df["limite"] * (1 - NEAR_THRESHOLD_PCT)
    proximo = df[(df["valor_num"] >= df["limite_inferior"]) & (df["valor_num"] < df["limite"])]
    counts = proximo.groupby("fornecedor").size()
    return proximo[proximo["fornecedor"].isin(counts[counts >= 3].index)].copy()


def _top_suppliers(conn: Any, year: int, empresa_id: str) -> tuple[pd.DataFrame, float]:
    # Aplicar o mesmo filtro de elementos: somente fornecedores de natureza "fornecimento de bens e serviços" (excluindo subvencoes sociais)
    sql = text("""
        SELECT f.codigo, f.descricao, f.empenhado
        FROM despesas_por_fornecedor f
        LEFT JOIN despesas_gerais g ON f.ano = g.ano AND f.descricao = g.nomefor
        WHERE f.ano = :ano AND f.empresa = :empresa
        AND g.elemento IN :elementos
    """).bindparams(
        bindparam("elementos", expanding=True, value=list(FORNECEDORES_NATUREZA_MAP.keys())),
    )

    df = pd.read_sql_query(sql, conn, params={"ano": year, "empresa": empresa_id})
    df["empenhado"] = _to_float(df["empenhado"])
    df = df.groupby(["codigo", "descricao"], as_index=False)["empenhado"].sum()

    total = df["empenhado"].sum()
    df["percentual"] = df["empenhado"] / total * 100 if total > 0 else 0

    top10 = df.nlargest(10, "empenhado").reset_index(drop=True)
    shares = df["empenhado"] / total if total > 0 else df["empenhado"] * 0
    hhi = float((shares**2).sum() * 10000)

    return top10, hhi


def _transfers_to_health(conn: Any, year: int, empresa_id: str) -> tuple[pd.DataFrame, float]:
    if empresa_id != SAUDE_EMPRESA:
        return pd.DataFrame(), 0.0
    df = pd.read_sql_query(
        text(
            "SELECT mes, entidade_pagadora, entidade_recebedora, repasse, devolucao FROM transferencias "
            "WHERE empresa = '7' AND ano = :ano AND UPPER(entidade_recebedora) LIKE '%SAUDE%'"
        ),
        conn,
        params={"ano": year},
    )
    if df.empty:
        return df, 0.0
    df["repasse_num"] = _to_float(df["repasse"])
    df["devolucao_num"] = _to_float(df["devolucao"])
    total = float((df["repasse_num"] - df["devolucao_num"]).sum())
    return df, total


def _budget_trend(conn: Any, empresa_id: str) -> "pd.DataFrame":
    df = pd.read_sql_query(
        text("""
            SELECT ano,
                   SUM(CAST(NULLIF(REPLACE(dotacao_atualizada, ',', '.'), '') AS FLOAT)) AS dotacao,
                   SUM(CAST(NULLIF(REPLACE(empenhado, ',', '.'), '') AS FLOAT)) AS empenhado
            FROM despesas_por_orgao
            WHERE empresa = :empresa
            GROUP BY ano
            ORDER BY ano
        """),
        conn,
        params={"empresa": empresa_id},
    )
    df["dotacao"] = _to_float(df["dotacao"])
    df["empenhado"] = _to_float(df["empenhado"])
    df["taxa"] = df.apply(lambda r: r["empenhado"] / r["dotacao"] if r["dotacao"] > 0 else 0.0, axis=1)
    return df


def _pharma_empenhos(conn: Any, year: int, empresa_id: str) -> dict:
    detail = pd.read_sql_query(
        text("""
            SELECT nomefor AS fornecedor, produ AS descricao,
                   SUM(CAST(NULLIF(REPLACE(empenhado, ',', '.'), '') AS FLOAT)) AS total
            FROM despesas_gerais
            WHERE empresa = :empresa AND ano = :ano
              AND subfuncao = '303'
              AND natureza = 'MATERIAL DE CONSUMO'
            GROUP BY nomefor, produ
            ORDER BY total DESC
        """),
        conn,
        params={"empresa": empresa_id, "ano": year},
    )
    detail["total"] = _to_float(detail["total"])
    trend = pd.read_sql_query(
        text("""
            SELECT ano,
                   SUM(CAST(NULLIF(REPLACE(empenhado, ',', '.'), '') AS FLOAT)) AS empenhado
            FROM despesas_gerais
            WHERE empresa = :empresa
              AND subfuncao = '303'
              AND natureza = 'MATERIAL DE CONSUMO'
            GROUP BY ano
            ORDER BY ano
        """),
        conn,
        params={"empresa": empresa_id},
    )
    trend["empenhado"] = _to_float(trend["empenhado"])
    if year not in trend["ano"].values:
        trend = pd.concat([trend, pd.DataFrame([{"ano": year, "empenhado": 0.0}])], ignore_index=True).sort_values(
            "ano"
        )
    return {
        "total": float(detail["total"].sum()) if not detail.empty else 0.0,
        "detail": detail,
        "trend": trend,
    }


def _pharma_judicial(conn: Any, year: int, empresa_id: str) -> dict:
    detail = pd.read_sql_query(
        text("""
            SELECT subfuncaonome AS subfuncao, nomefor AS fornecedor, produ AS descricao,
                   SUM(CAST(NULLIF(REPLACE(empenhado, ',', '.'), '') AS FLOAT)) AS total
            FROM despesas_gerais
            WHERE empresa = :empresa AND ano = :ano
              AND elemento = '91'
            GROUP BY subfuncaonome, nomefor, produ
            ORDER BY total DESC
        """),
        conn,
        params={"empresa": empresa_id, "ano": year},
    )
    detail["total"] = _to_float(detail["total"])
    return {
        "total": float(detail["total"].sum()) if not detail.empty else 0.0,
        "detail": detail,
    }


def _pharma_licitacoes(conn: Any, year: int, empresa_id: str) -> pd.DataFrame:
    df = pd.read_sql_query(
        text("""
            SELECT numero, modalidade, discr AS objeto, valor, situacao, data_abertura
            FROM licitacoes
            WHERE empresa = :empresa AND ano = :ano
              AND (
                UPPER(discr) LIKE '%MEDICAMENTO%'
                OR UPPER(discr) LIKE '%INSUMO%'
                OR UPPER(discr) LIKE '%FARMAC%'
                OR UPPER(discr) LIKE '%MATERIAL HOSPITALAR%'
                OR UPPER(discr) LIKE '%CORRELATO%'
              )
            ORDER BY CAST(NULLIF(REPLACE(valor, ',', '.'), '') AS FLOAT) DESC NULLS LAST
        """),
        conn,
        params={"empresa": empresa_id, "ano": year},
    )
    if not df.empty:
        df["valor_num"] = _to_float(df["valor"])
    return df


def _top_suppliers_services(conn: Any, year: int, empresa_id: str) -> pd.DataFrame:
    query = text("""
        SELECT fornecedor, objeto, SUM(CAST(NULLIF(REPLACE(valcon, ',', '.'), '') AS FLOAT)) as total
        FROM contratos
        WHERE ano = :ano AND empresa = :empresa
        GROUP BY fornecedor, objeto
        ORDER BY total DESC
    """)
    df = pd.read_sql_query(query, conn, params={"ano": year, "empresa": empresa_id})
    df["total"] = _to_float(df["total"])
    return df


def run(conn: Any, year: int, empresa_id: str = SAUDE_EMPRESA) -> dict:
    emendas_df, emendas_total = _emendas(conn, year, empresa_id)
    orcamento = _budget(conn, year, empresa_id)
    tendencia_execucao = _execution_trend(conn, empresa_id)
    fluxo_execucao = _execution_flow(conn, year, empresa_id)
    contratos_por_modalidade = _contracts_by_modality(conn, year, empresa_id)
    adesao_df, adesao_value = _adesao_de_ata(conn, year, empresa_id)
    gaps_licitacao = _licitacao_gaps(conn, year, empresa_id)
    principais_fornecedores, hhi = _top_suppliers(conn, year, empresa_id)
    principais_fornecedores_servicos = _top_suppliers_services(conn, year, empresa_id)
    fracionamento = _splitting(conn, year, empresa_id)
    transferencias_df, transferencias_total = _transfers_to_health(conn, year, empresa_id)
    pharma_empenhos = _pharma_empenhos(conn, year, empresa_id)
    pharma_judicial = _pharma_judicial(conn, year, empresa_id)
    pharma_licitacoes = _pharma_licitacoes(conn, year, empresa_id)
    tendencia_orcamento = _budget_trend(conn, empresa_id)
    return {  # noqa: RET504
        "emendas": emendas_df,
        "emendas_total": emendas_total,
        "orcamento": orcamento,
        "tendencia_execucao": tendencia_execucao,
        "fluxo_execucao": fluxo_execucao,
        "contratos_por_modalidade": contratos_por_modalidade,
        "adesao_de_ata_list": adesao_df,
        "adesao_de_ata_count": len(adesao_df),
        "adesao_de_ata_contracts_linked": int(adesao_df["tem_contrato"].sum()) if not adesao_df.empty else 0,
        "adesao_de_ata_value": adesao_value,
        "licitacao_gaps": gaps_licitacao,
        "principais_fornecedores": principais_fornecedores,
        "principais_fornecedores_servicos": principais_fornecedores_servicos,
        "hhi": hhi,
        "fracionamento": fracionamento,
        "transferencias_saude": transferencias_df,
        "transferencias_saude_total": transferencias_total,
        "pharma_empenhos": pharma_empenhos,
        "pharma_judicial": pharma_judicial,
        "pharma_licitacoes": pharma_licitacoes,
        "tendencia_orcamento": tendencia_orcamento,
    }


def get_principais_servicos_por_fornecedor(
    services_df: "pd.DataFrame", top_supplier_names: "pd.Series", n: int = 3
) -> "pd.DataFrame":
    filtered = services_df[services_df["fornecedor"].isin(top_supplier_names)]
    return filtered.sort_values(["fornecedor", "total"], ascending=[True, False]).groupby("fornecedor").head(n)
