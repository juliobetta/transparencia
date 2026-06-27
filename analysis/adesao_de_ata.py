from typing import Any, Optional

import pandas as pd
from sqlalchemy import text


def _to_float(series: pd.Series) -> pd.Series:
    return pd.to_numeric(series.astype(str).str.replace(",", "."), errors="coerce").fillna(0)


def run(conn: Any, year: int, empresa_id: str) -> dict:
    query = text("""
        SELECT
            l.numero,
            :ano as ano,
            l.discr as objeto,
            l.valor as licitacao_valor,
            SUM(CAST(NULLIF(REPLACE(c.valcon, ',', '.'), '') AS FLOAT)) as total_c_valor,
            SUM(CAST(NULLIF(REPLACE(c.empenhado, ',', '.'), '') AS FLOAT)) as total_c_empenhado,
            l.carona,
            c.mes
        FROM licitacoes l
        LEFT JOIN contratos c
            ON c.licitacao_numero = l.numero
            AND c.ano = l.ano
            AND c.empresa = l.empresa
        WHERE l.ano = :ano AND l.empresa = :empresa
        GROUP BY l.numero, l.discr, l.valor, l.carona, c.mes
    """)
    try:
        df = pd.read_sql_query(query, conn, params={"ano": year, "empresa": empresa_id})

        if "total_c_valor" in df.columns:
            df["total_c_valor"] = df["total_c_valor"].fillna(0)

        df["carona_clean"] = df["carona"].fillna("").astype(str).str.strip().str.upper()
        df = df[df["carona_clean"] == "S"]

        if df.empty:
            return {
                "list": pd.DataFrame(),
                "count": 0,
                "value": 0.0,
                "total_licitacao": 0.0,
                "contracts_linked_count": 0,
            }

        total_value = float(_to_float(df["total_c_valor"]).sum())
        total_licitacao = float(_to_float(df["licitacao_valor"]).sum())
        df["has_contract"] = _to_float(df["total_c_valor"]) > 0

        return {
            "list": df,
            "count": len(df),
            "value": total_value,
            "total_licitacao": total_licitacao,
            "contracts_linked_count": int(df["has_contract"].sum()),
        }
    except Exception as e:
        print(f"DEBUG: Exception in Adesao: {e}")
        return {"list": pd.DataFrame(), "count": 0, "value": 0.0, "total_licitacao": 0.0, "contracts_linked_count": 0}


def formal_counts_by_year(conn: Any, years: list[int], empresa_id: str = "2") -> dict[int, int]:
    placeholders = ", ".join(str(y) for y in years)
    df = pd.read_sql_query(
        text(f"SELECT ano FROM licitacoes WHERE ano IN ({placeholders}) AND empresa = :empresa AND carona = 'S'"),
        conn,
        params={"empresa": empresa_id},
    )
    counts = df.groupby("ano").size()
    return {y: int(counts.get(y, 0)) for y in years}


def external_counts_by_year(conn: Any, years: list[int], empresa_id: Optional[str] = None) -> dict[int, int]:
    placeholders = ", ".join(str(y) for y in years)
    empresa_clause = "AND empresa = :empresa" if empresa_id else ""
    params: dict = {}
    if empresa_id:
        params["empresa"] = empresa_id
    df = pd.read_sql_query(
        text(f"""
            SELECT ano FROM despesas_gerais
            WHERE ano IN ({placeholders})
              {empresa_clause}
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
    """Find empenhos whose justification text references an external ata de adesão.

    These are spending records where the municipality joined another entity's
    Ata de Registro de Preços (TERMO DE ADESÃO EXTERNA), which may not appear
    in the licitacoes table with carona='S'.
    """
    empresa_clause = "AND dg.empresa = :empresa" if empresa_id else ""
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
          {empresa_clause}
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
            return {"list": pd.DataFrame(), "count": 0, "total_pago": 0.0}
        df["pago"] = _to_float(df["pago"])
        return {
            "list": df,
            "count": len(df),
            "total_pago": float(df["pago"].sum()),
        }
    except Exception as e:
        print(f"DEBUG: Exception in Adesao Externa: {e}")
        return {"list": pd.DataFrame(), "count": 0, "total_pago": 0.0}
