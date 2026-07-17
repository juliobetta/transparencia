from typing import Any

import pandas as pd
from sqlalchemy import text

from analysis import fontes_receita


def distribuicao_salarios(conn: Any, year: int) -> pd.DataFrame:
    """Retorna proventos positivos para exibição em histograma (estornos excluídos — apenas visualização)."""
    df = pd.read_sql_query(text("SELECT proventos FROM fct_pessoal WHERE ano = :ano"), conn, params={"ano": year})
    df["proventos"] = pd.to_numeric(df["proventos"].astype(str).str.replace(",", "."), errors="coerce")
    return df[df["proventos"] > 0].dropna()


def run(conn: Any, years: list[int], empresa_ids: list[str] | None = None) -> pd.DataFrame:
    # pessoal usa empresa='001' (código retornado pela API, não mapeado para as entidades do dashboard)
    # — a folha é um dado municipal consolidado e não deve ser filtrada por empresa_ids.
    empresa_clause = "AND empresa = ANY(:empresas)" if empresa_ids else ""
    records = []
    for year in years:
        folha = pd.read_sql_query(
            text("SELECT proventos FROM fct_pessoal WHERE ano = :ano"),
            conn,
            params={"ano": year},
        )
        total_folha = (
            pd.to_numeric(folha["proventos"].astype(str).str.replace(",", "."), errors="coerce").fillna(0).sum()
        )

        pago_params: dict = {"ano": year}
        if empresa_ids:
            pago_params["empresas"] = empresa_ids
        pago = pd.read_sql_query(
            text(f"SELECT pago FROM raw_porciuncula_prefeitura.despesas_por_orgao WHERE ano = :ano {empresa_clause}"),
            conn,
            params=pago_params,
        )
        total_pago = pd.to_numeric(pago["pago"].astype(str).str.replace(",", "."), errors="coerce").fillna(0).sum()

        rev_df = fontes_receita.run(conn, [year], empresa_ids=empresa_ids)
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
        SELECT
            SUM(empenhado) as empenhado_bruto,
            SUM(empenhado_liquido) as empenhado_liquido,
            SUM(liquidado) as liquidado,
            SUM(pago) as pago
        FROM fct_despesas
        WHERE ano = :ano
          AND elemento IN ('01', '03', '11', '96')
          AND (descricao ILIKE '%13%' OR descricao ILIKE '%decimo terceiro%' OR descricao ILIKE '%décimo terceiro%')
          AND descricao NOT ILIKE '%anula%'
          AND descricao NOT ILIKE '%136%'
          AND descricao NOT ILIKE '%137%'
          AND descricao NOT ILIKE '%138%'
          AND descricao NOT ILIKE '%139%'
          AND tipo_empenho != 'AN'
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
        SELECT
            COALESCE(empresa_nome, empresa_id) as orgao,
            COALESCE(funcao_nome, 'Outros') as funcao,
            SUM(empenhado) as empenhado_bruto,
            SUM(empenhado_liquido) as empenhado_liquido,
            SUM(liquidado) as liquidado,
            SUM(pago) as pago
        FROM fct_despesas
        WHERE ano = :ano
          AND elemento IN ('01', '03', '11', '96')
          AND (descricao ILIKE '%13%' OR descricao ILIKE '%decimo terceiro%' OR descricao ILIKE '%décimo terceiro%')
          AND descricao NOT ILIKE '%anula%'
          AND descricao NOT ILIKE '%136%'
          AND descricao NOT ILIKE '%137%'
          AND descricao NOT ILIKE '%138%'
          AND descricao NOT ILIKE '%139%'
          AND tipo_empenho != 'AN'
        GROUP BY empresa_nome, empresa_id, funcao_nome
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
