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


def total_decimo_terceiro(conn: Any, year: int) -> float | None:
    """Calcula o total pago referente ao 13º salário consultando despesas_gerais."""
    query = """
        SELECT SUM(CAST(REPLACE(pago, ',', '.') AS NUMERIC))
        FROM despesas_gerais
        WHERE ano = :ano
          AND elemento IN ('01', '03', '11', '96')
          AND (produ ILIKE '%13%' OR produ ILIKE '%decimo terceiro%' OR produ ILIKE '%décimo terceiro%')
          AND produ NOT ILIKE '%anula%'
          AND produ NOT ILIKE '%136%'
          AND produ NOT ILIKE '%137%'
          AND produ NOT ILIKE '%138%'
          AND produ NOT ILIKE '%139%'
    """
    df = pd.read_sql_query(text(query), conn, params={"ano": year})
    if df.empty or pd.isna(df.iloc[0, 0]):
        return None
    return float(df.iloc[0, 0])
