from typing import Any

import pandas as pd
from sqlalchemy import text

from analysis import revenue_sources


def salary_distribution(conn: Any, year: int) -> pd.DataFrame:
    """Return positive proventos for histogram display (reversals excluded — display only)."""
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

        # Use total receita as RCL proxy (LRF Art. 20, III, b requires RCL as denominator).
        # "total" uses arrecadado when available, previsto as fallback for historical years.
        rev_df = revenue_sources.run(conn, [year])
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
