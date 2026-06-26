from typing import Any

import pandas as pd
from sqlalchemy import text


def run(conn: Any, years: list[int]) -> pd.DataFrame:
    records = []
    for year in years:
        folha = pd.read_sql_query(text("SELECT proventos FROM pessoal WHERE ano = :ano"), conn, params={"ano": year})
        total_folha = pd.to_numeric(folha["proventos"].str.replace(",", "."), errors="coerce").fillna(0).sum()

        gasto = pd.read_sql_query(
            text("SELECT pago FROM despesas_por_orgao WHERE ano = :ano"), conn, params={"ano": year}
        )
        total_gasto = pd.to_numeric(gasto["pago"].str.replace(",", "."), errors="coerce").fillna(0).sum()

        percentual = total_folha / total_gasto * 100 if total_gasto > 0 else 0
        records.append(
            {"ano": year, "total_folha": total_folha, "total_gasto": total_gasto, "percentual_folha": percentual}
        )
    return pd.DataFrame(records)
