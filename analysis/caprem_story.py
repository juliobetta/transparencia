from typing import Any

import pandas as pd
from sqlalchemy import text

CAPREM_CODE = "1061"


def run(conn: Any, year: int):
    df = pd.read_sql_query(
        text("SELECT * FROM despesas_por_fornecedor WHERE codigo = :codigo AND ano = :ano"),
        conn,
        params={"codigo": CAPREM_CODE, "ano": year},
    )

    if not df.empty:
        for col in ["empenhado", "liquidado", "pago"]:
            df[col] = pd.to_numeric(df[col].str.replace(",", "."), errors="coerce").fillna(0)

        total_transfers = df["empenhado"].sum()
        count_operations = len(df)
    else:
        total_transfers = 0
        count_operations = 0

    return {
        "total_transfers": total_transfers,
        "count_operations": count_operations,
        "despesas": df,
        "transfers_by_type": [],
        "budget": {"dotacao": 0, "empenhado": 0, "taxa_execucao": 0},
    }
