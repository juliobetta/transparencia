from typing import Any

import pandas as pd
from sqlalchemy import text


def _to_float(series: pd.Series) -> pd.Series:
    return pd.to_numeric(series.astype(str).str.replace(",", "."), errors="coerce").fillna(0)


def run(conn: Any, year: int, empresa_ids: list[str] | None = None) -> dict:
    empresa_clausula_c = "AND c.empresa_id = ANY(:empresas)" if empresa_ids else ""
    empresa_clausula_l = "AND l.empresa_id = ANY(:empresas)" if empresa_ids else ""
    # União de duas partes:
    # 1. Contratos assinados neste ano cuja licitação tem carona='S' (licitação de qualquer ano)
    # 2. Licitações carona criadas neste ano que ainda não possuem contratos
    query = text(f"""
        SELECT
            l.licitacao_numero AS numero,
            l.discriminacao AS objeto,
            l.valor AS licitacao_valor,
            l.carona,
            c.mes,
            CAST(NULLIF(REPLACE(c.valor_contrato, ',', '.'), '') AS FLOAT) AS c_valor,
            CAST(NULLIF(REPLACE(c.empenhado, ',', '.'), '') AS FLOAT) AS c_empenhado
        FROM fct_contratos c
        JOIN fct_licitacoes l
            ON l.licitacao_numero = c.licitacao_numero
            AND l.empresa_id = c.empresa_id
            AND l.carona = 'S'
        WHERE c.ano = :ano
          {empresa_clausula_c}

        UNION ALL

        SELECT
            l.licitacao_numero AS numero,
            l.discriminacao AS objeto,
            l.valor AS licitacao_valor,
            l.carona,
            NULL AS mes,
            0 AS c_valor,
            0 AS c_empenhado
        FROM fct_licitacoes l
        WHERE l.ano = :ano AND l.carona = 'S'
          {empresa_clausula_l}
          AND NOT EXISTS (
              SELECT 1 FROM fct_contratos c2
              WHERE c2.licitacao_numero = l.licitacao_numero AND c2.empresa_id = l.empresa_id
          )
    """)
    params: dict = {"ano": year}
    if empresa_ids:
        params["empresas"] = empresa_ids
    try:
        raw = pd.read_sql_query(query, conn, params=params)

        if raw.empty:
            return {
                "lista": pd.DataFrame(),
                "quantidade": 0,
                "valor": 0.0,
                "total_licitacao": 0.0,
                "contratos_associados_count": 0,
            }

        df = raw.groupby(["numero", "objeto", "licitacao_valor", "carona"], as_index=False).agg(
            total_c_valor=("c_valor", "sum"), total_c_empenhado=("c_empenhado", "sum"), mes=("mes", "first")
        )

        total_value = float(df["total_c_valor"].sum())
        total_licitacao = float(_to_float(df["licitacao_valor"]).sum())
        df["tem_contrato"] = df["total_c_valor"] > 0
        df["periodo"] = df["mes"].apply(lambda m: str(int(m)).zfill(2) if pd.notna(m) else "") + "/" + str(year)

        return {
            "lista": df,
            "quantidade": len(df),
            "valor": total_value,
            "total_licitacao": total_licitacao,
            "contratos_associados_count": int(df["tem_contrato"].sum()),
        }
    except Exception:
        return {
            "lista": pd.DataFrame(),
            "quantidade": 0,
            "valor": 0.0,
            "total_licitacao": 0.0,
            "contratos_associados_count": 0,
        }


def formal_counts_by_year(conn: Any, years: list[int], empresa_ids: list[str] | None = None) -> dict[int, int]:
    placeholders = ", ".join(str(y) for y in years)
    empresa_clausula = "AND empresa_id = ANY(:empresas)" if empresa_ids else ""
    params: dict = {"empresas": empresa_ids} if empresa_ids else {}
    df = pd.read_sql_query(
        text(f"SELECT ano FROM fct_licitacoes WHERE ano IN ({placeholders}) AND carona = 'S' {empresa_clausula}"),
        conn,
        params=params,
    )
    counts = df.groupby("ano").size()
    return {y: int(counts.get(y, 0)) for y in years}


def external_counts_by_year(conn: Any, years: list[int], empresa_ids: list[str] | None = None) -> dict[int, int]:
    placeholders = ", ".join(str(y) for y in years)
    empresa_clausula = "AND empresa_id = ANY(:empresas)" if empresa_ids else ""
    params: dict = {}
    if empresa_ids:
        params["empresas"] = empresa_ids
    df = pd.read_sql_query(
        text(f"""
            SELECT ano FROM fct_despesas
            WHERE ano IN ({placeholders})
              {empresa_clausula}
              AND (
                  UPPER(descricao) LIKE '%ATA DE REGISTRO DE PRE%'
                  OR UPPER(descricao) LIKE '%ADESAO%ATA%'
                  OR UPPER(descricao) LIKE '%ADESÃO%ATA%'
                  OR UPPER(descricao) LIKE '%TERMO DE ADESÃO%'
                  OR UPPER(descricao) LIKE '%TERMO DE ADESAO%'
              )
        """),
        conn,
        params=params,
    )
    counts = df.groupby("ano").size()
    return {y: int(counts.get(y, 0)) for y in years}


def run_external(conn: Any, year: int, empresa_ids: list[str] | None = None) -> dict:
    """Encontrar empenhos cujo texto de justificativa referencia uma ata de adesão externa.

    São registros de despesa em que o município aderiu à Ata de Registro de Preços
    de outra entidade (TERMO DE ADESÃO EXTERNA), que podem não aparecer
    na tabela licitacoes com carona='S'.
    """
    empresa_clausula = "AND dg.empresa_id = ANY(:empresas)" if empresa_ids else ""
    params: dict = {"ano": year}
    if empresa_ids:
        params["empresas"] = empresa_ids

    query = text(f"""
        SELECT
            dg.data_empenho AS data,
            dg.fornecedor_nome AS fornecedor,
            dg.pago AS pago,
            dg.empresa_id AS unidade,
            dg.descricao AS justificativa,
            dg.licitacao_numero AS num_licitacao
        FROM fct_despesas dg
        WHERE dg.ano = :ano
          {empresa_clausula}
          AND (
              UPPER(dg.descricao) LIKE '%ATA DE REGISTRO DE PRE%'
              OR UPPER(dg.descricao) LIKE '%ADESAO%ATA%'
              OR UPPER(dg.descricao) LIKE '%ADESÃO%ATA%'
              OR UPPER(dg.descricao) LIKE '%TERMO DE ADESÃO%'
              OR UPPER(dg.descricao) LIKE '%TERMO DE ADESAO%'
          )
        ORDER BY CAST(NULLIF(REPLACE(dg.pago, ',', '.'), '') AS FLOAT) DESC
    """)

    try:
        df = pd.read_sql_query(query, conn, params=params)
        if df.empty:
            return {"lista": pd.DataFrame(), "quantidade": 0, "total_pago": 0.0}
        df["pago"] = _to_float(df["pago"])
        df["data"] = pd.to_datetime(df["data"], dayfirst=True, errors="coerce").dt.date
        return {
            "lista": df,
            "quantidade": len(df),
            "total_pago": float(df["pago"].sum()),
        }
    except Exception as e:
        print(f"DEBUG: Exception in Adesao Externa: {e}")
        return {"lista": pd.DataFrame(), "quantidade": 0, "total_pago": 0.0}
