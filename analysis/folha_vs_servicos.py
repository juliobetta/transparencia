from typing import Any

import pandas as pd
from sqlalchemy import text

from analysis import fontes_receita


def distribuicao_salarios(conn: Any, year: int) -> pd.DataFrame:
    """Retorna proventos positivos para exibição em histograma (estornos excluídos — apenas visualização)."""
    df = pd.read_sql_query(text("SELECT proventos FROM pessoal WHERE ano = :ano"), conn, params={"ano": year})
    df["proventos"] = pd.to_numeric(df["proventos"].str.replace(",", "."), errors="coerce")
    return df[df["proventos"] > 0].dropna()


def run(conn: Any, years: list[int]) -> pd.DataFrame:
    records = []
    for year in years:
        folha = pd.read_sql_query(text("SELECT proventos FROM pessoal WHERE ano = :ano"), conn, params={"ano": year})
        total_folha = pd.to_numeric(folha["proventos"].str.replace(",", "."), errors="coerce").fillna(0).sum()

        pago = pd.read_sql_query(
            text("SELECT pago FROM despesas_por_orgao WHERE ano = :ano"), conn, params={"ano": year}
        )
        total_pago = pd.to_numeric(pago["pago"].str.replace(",", "."), errors="coerce").fillna(0).sum()

        # Usa total de receita como proxy da RCL (LRF Art. 20, III, b exige RCL como denominador).
        # "total" usa arrecadado quando disponível, previsto como fallback para anos históricos.
        rev_df = fontes_receita.run(conn, [year])
        rcl_proxy = float(rev_df.iloc[0]["total"]) if not rev_df.empty else 0.0

        percentual = total_folha / rcl_proxy * 100 if rcl_proxy > 0 else 0
        records.append(
            {
                "ano": year,
                "total_folha": total_folha,
                "total_pago": total_pago,
                "rcl_proxy": rcl_proxy,
                "percentual_folha": percentual,
            }
        )
    return pd.DataFrame(records)


def execucao_decimo_terceiro(conn: Any, year: int) -> dict[str, float] | None:
    """Calcula a execução orçamentária do 13º salário consultando despesas_gerais."""
    query = """
        WITH empenhos_13 AS (
            SELECT
                pkemp,
                CAST(REPLACE(empenhado, ',', '.') AS NUMERIC) as empenhado,
                CAST(REPLACE(liquidado, ',', '.') AS NUMERIC) as liquidado,
                CAST(REPLACE(pago, ',', '.') AS NUMERIC) as pago
            FROM despesas_gerais
            WHERE ano = :ano
              AND elemento IN ('01', '03', '11', '96')
              AND (produ ILIKE '%13%' OR produ ILIKE '%decimo terceiro%' OR produ ILIKE '%décimo terceiro%')
              AND produ NOT ILIKE '%anula%'
              AND produ NOT ILIKE '%136%'
              AND produ NOT ILIKE '%137%'
              AND produ NOT ILIKE '%138%'
              AND produ NOT ILIKE '%139%'
              AND tpem != 'AN'
        ),
        anulacoes AS (
            SELECT
                pkempa,
                SUM(CAST(REPLACE(empenhado, ',', '.') AS NUMERIC)) as tot_anulado
            FROM despesas_gerais
            WHERE ano = :ano AND tpem = 'AN'
            GROUP BY pkempa
        )
        SELECT
            SUM(e.empenhado) as empenhado_bruto,
            SUM(e.empenhado + COALESCE(a.tot_anulado, 0)) as empenhado_liquido,
            SUM(e.liquidado) as liquidado,
            SUM(e.pago) as pago
        FROM empenhos_13 e
        LEFT JOIN anulacoes a ON e.pkemp = a.pkempa
    """
    df = pd.read_sql_query(text(query), conn, params={"ano": year})
    if df.empty or pd.isna(df.iloc[0]["empenhado_bruto"]) or df.iloc[0]["empenhado_bruto"] is None:
        return None

    emp_bruto = float(df.iloc[0]["empenhado_bruto"])
    emp_liq = float(df.iloc[0]["empenhado_liquido"]) if not pd.isna(df.iloc[0]["empenhado_liquido"]) else emp_bruto
    liq = float(df.iloc[0]["liquidado"]) if not pd.isna(df.iloc[0]["liquidado"]) else 0.0
    pag = float(df.iloc[0]["pago"]) if not pd.isna(df.iloc[0]["pago"]) else 0.0

    pct_pago = (pag / emp_liq) if emp_liq > 0 else 0.0

    return {
        "empenhado": emp_liq,
        "empenhado_bruto": emp_bruto,
        "liquidado": liq,
        "pago": pag,
        "pct_pago": pct_pago,
    }


def detalhe_decimo_terceiro(conn: Any, year: int) -> pd.DataFrame:
    """Retorna o detalhamento da execução orçamentária do 13º salário por Órgão e Função."""
    query = """
        WITH empenhos_13 AS (
            SELECT
                pkemp,
                nomeempresa as orgao,
                COALESCE(funcaonome, 'Outros') as funcao,
                CAST(REPLACE(empenhado, ',', '.') AS NUMERIC) as empenhado,
                CAST(REPLACE(liquidado, ',', '.') AS NUMERIC) as liquidado,
                CAST(REPLACE(pago, ',', '.') AS NUMERIC) as pago
            FROM despesas_gerais
            WHERE ano = :ano
              AND elemento IN ('01', '03', '11', '96')
              AND (produ ILIKE '%13%' OR produ ILIKE '%decimo terceiro%' OR produ ILIKE '%décimo terceiro%')
              AND produ NOT ILIKE '%anula%'
              AND produ NOT ILIKE '%136%'
              AND produ NOT ILIKE '%137%'
              AND produ NOT ILIKE '%138%'
              AND produ NOT ILIKE '%139%'
              AND tpem != 'AN'
        ),
        anulacoes AS (
            SELECT
                pkempa,
                SUM(CAST(REPLACE(empenhado, ',', '.') AS NUMERIC)) as tot_anulado
            FROM despesas_gerais
            WHERE ano = :ano AND tpem = 'AN'
            GROUP BY pkempa
        )
        SELECT
            e.orgao,
            e.funcao,
            SUM(e.empenhado) as empenhado_bruto,
            SUM(e.empenhado + COALESCE(a.tot_anulado, 0)) as empenhado_liquido,
            SUM(e.liquidado) as liquidado,
            SUM(e.pago) as pago
        FROM empenhos_13 e
        LEFT JOIN anulacoes a ON e.pkemp = a.pkempa
        GROUP BY e.orgao, e.funcao
        ORDER BY pago DESC
    """
    df = pd.read_sql_query(text(query), conn, params={"ano": year})
    if df.empty:
        return pd.DataFrame(columns=["orgao", "funcao", "empenhado", "liquidado", "pago", "pct_pago"])

    df["empenhado_bruto"] = pd.to_numeric(df["empenhado_bruto"], errors="coerce").fillna(0.0)
    df["empenhado_liquido"] = pd.to_numeric(df["empenhado_liquido"], errors="coerce").fillna(0.0)
    df["liquidado"] = pd.to_numeric(df["liquidado"], errors="coerce").fillna(0.0)
    df["pago"] = pd.to_numeric(df["pago"], errors="coerce").fillna(0.0)
    df["pct_pago"] = (df["pago"] / df["empenhado_liquido"] * 100.0).where(df["empenhado_liquido"] > 0, 0.0)

    # Use empenhado_liquido as the main 'empenhado' column for UI
    df["empenhado"] = df["empenhado_liquido"]

    return df[["orgao", "funcao", "empenhado", "liquidado", "pago", "pct_pago"]]
