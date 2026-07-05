from typing import Any, Optional

import pandas as pd
from sqlalchemy import text


def _to_float(series: pd.Series) -> pd.Series:
    return pd.to_numeric(series.astype(str).str.replace(",", "."), errors="coerce").fillna(0)


def run(conn: Any, year: int, empresa_id: Optional[str] = None) -> dict:
    empresa_clausula_c = "AND c.empresa = :empresa" if empresa_id else ""
    empresa_clausula_l = "AND l.empresa = :empresa" if empresa_id else ""
    # União de duas partes:
    # 1. Contratos assinados neste ano cuja licitação tem carona='S' (licitação de qualquer ano)
    # 2. Licitações carona criadas neste ano que ainda não possuem contratos
    query = text(f"""
        SELECT
            l.numero,
            l.discr AS objeto,
            l.valor AS licitacao_valor,
            l.carona,
            c.mes,
            CAST(NULLIF(REPLACE(c.valcon, ',', '.'), '') AS FLOAT)    AS c_valor,
            CAST(NULLIF(REPLACE(c.empenhado, ',', '.'), '') AS FLOAT) AS c_empenhado
        FROM contratos c
        JOIN licitacoes l
            ON l.numero = c.licitacao_numero
            AND l.empresa = c.empresa
            AND l.carona = 'S'
        WHERE c.ano = :ano
          {empresa_clausula_c}

        UNION ALL

        SELECT
            l.numero,
            l.discr AS objeto,
            l.valor AS licitacao_valor,
            l.carona,
            NULL    AS mes,
            0       AS c_valor,
            0       AS c_empenhado
        FROM licitacoes l
        WHERE l.ano = :ano AND l.carona = 'S'
          {empresa_clausula_l}
          AND NOT EXISTS (
              SELECT 1 FROM contratos c2
              WHERE c2.licitacao_numero = l.numero AND c2.empresa = l.empresa
          )
    """)
    params: dict = {"ano": year}
    if empresa_id:
        params["empresa"] = empresa_id
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
    except Exception as e:
        print(f"DEBUG: Exception in Adesao: {e}")
        return {
            "list": pd.DataFrame(),
            "count": 0,
            "value": 0.0,
            "total_licitacao": 0.0,
            "contratos_associados_count": 0,
        }


def formal_counts_by_year(conn: Any, years: list[int], empresa_id: Optional[str] = None) -> dict[int, int]:
    placeholders = ", ".join(str(y) for y in years)
    empresa_clausula = "AND empresa = :empresa" if empresa_id else ""
    params: dict = {"empresa": empresa_id} if empresa_id else {}
    df = pd.read_sql_query(
        text(f"SELECT ano FROM licitacoes WHERE ano IN ({placeholders}) AND carona = 'S' {empresa_clausula}"),
        conn,
        params=params,
    )
    counts = df.groupby("ano").size()
    return {y: int(counts.get(y, 0)) for y in years}


def external_counts_by_year(conn: Any, years: list[int], empresa_id: Optional[str] = None) -> dict[int, int]:
    placeholders = ", ".join(str(y) for y in years)
    empresa_clausula = "AND empresa = :empresa" if empresa_id else ""
    params: dict = {}
    if empresa_id:
        params["empresa"] = empresa_id
    df = pd.read_sql_query(
        text(f"""
            SELECT ano FROM despesas_gerais
            WHERE ano IN ({placeholders})
              {empresa_clausula}
              AND (
                  UPPER(produ) LIKE '%ATA DE REGISTRO DE PRE%'
                  OR UPPER(produ) LIKE '%ADESAO%ATA%'
                  OR UPPER(produ) LIKE '%ADESÃO%ATA%'
                  OR UPPER(produ) LIKE '%TERMO DE ADESÃO%'
                  OR UPPER(produ) LIKE '%TERMO DE ADESAO%'
              )
        """),
        conn,
        params=params,
    )
    counts = df.groupby("ano").size()
    return {y: int(counts.get(y, 0)) for y in years}


def run_external(conn: Any, year: int, empresa_id: Optional[str] = None) -> dict:
    """Encontrar empenhos cujo texto de justificativa referencia uma ata de adesão externa.

    São registros de despesa em que o município aderiu à Ata de Registro de Preços
    de outra entidade (TERMO DE ADESÃO EXTERNA), que podem não aparecer
    na tabela licitacoes com carona='S'.
    """
    empresa_clausula = "AND dg.empresa = :empresa" if empresa_id else ""
    params: dict = {"ano": year}
    if empresa_id:
        params["empresa"] = empresa_id

    query = text(f"""
        SELECT
            dg.datae      AS data,
            dg.nomefor    AS fornecedor,
            dg.pago       AS pago,
            dg.nomeempresa AS unidade,
            dg.produ      AS justificativa,
            dg.numlicit   AS num_licitacao
        FROM despesas_gerais dg
        WHERE dg.ano = :ano
          {empresa_clausula}
          AND (
              UPPER(dg.produ) LIKE '%ATA DE REGISTRO DE PRE%'
              OR UPPER(dg.produ) LIKE '%ADESAO%ATA%'
              OR UPPER(dg.produ) LIKE '%ADESÃO%ATA%'
              OR UPPER(dg.produ) LIKE '%TERMO DE ADESÃO%'
              OR UPPER(dg.produ) LIKE '%TERMO DE ADESAO%'
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
