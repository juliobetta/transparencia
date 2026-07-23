from typing import Any

import pandas as pd
from sqlalchemy import text


def _to_float(series: pd.Series) -> pd.Series:
    return pd.to_numeric(series.astype(str).str.replace(",", "."), errors="coerce").fillna(0)


def run(conn: Any, year: int, empresa_ids: list[str] | None = None) -> dict:
    empresa_clausula = "AND l.empresa_id = ANY(:empresas)" if empresa_ids else ""
    params: dict = {"ano": year}
    if empresa_ids:
        params["empresas"] = empresa_ids

    query = text(f"""
        select
            l.licitacao_numero as numero,
            coalesce(l.discriminacao, l.licitacao_numero) as objeto,
            l.valor as licitacao_valor,
            l.carona,
            c.mes,
            coalesce(c.valor_contrato, 0) as c_valor,
            coalesce(c.empenhado, 0) as c_empenhado
        from fct_licitacoes l
        left join fct_contratos c
            on c.licitacao_numero = l.licitacao_numero
            and c.empresa_id = l.empresa_id
        where l.ano = :ano and l.carona = 'S'
          {empresa_clausula}
    """)
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
            total_c_valor=("c_valor", "sum"),
            total_c_empenhado=("c_empenhado", "sum"),
            mes=("mes", "first"),
        )

        total_value = float(df["total_c_valor"].sum())
        total_licitacao = float(_to_float(df["licitacao_valor"]).sum())
        df["tem_contrato"] = df["total_c_valor"] > 0
        df["periodo"] = df["mes"].apply(lambda m: str(int(m)).zfill(2) if pd.notna(m) and m else "") + "/" + str(year)

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
            dg.empenhado AS empenhado,
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
        ORDER BY dg.pago DESC
    """)

    try:
        df = pd.read_sql_query(query, conn, params=params)
        if df.empty:
            return {"lista": pd.DataFrame(), "quantidade": 0, "total_pago": 0.0}
        df["pago"] = _to_float(df["pago"])
        df["empenhado"] = _to_float(df["empenhado"])
        df["data"] = pd.to_datetime(df["data"], dayfirst=True, errors="coerce").dt.date
        return {
            "lista": df,
            "quantidade": len(df),
            "total_pago": float(df["pago"].sum()),
        }
    except Exception as e:
        print(f"DEBUG: Exception in Adesao Externa: {e}")
        return {"lista": pd.DataFrame(), "quantidade": 0, "total_pago": 0.0}
