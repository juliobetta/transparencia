from typing import Any

import pandas as pd
from sqlalchemy import text

# codigo de fornecedor do CAPREM no banco de dados
# TODO: mover para metadata ou config
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

        total_transferencias = df["empenhado"].sum()
        count_operacoes = len(df)
    else:
        total_transferencias = 0
        count_operacoes = 0

    return {
        "total_transferencias": total_transferencias,
        "count_operacoes": count_operacoes,
        "despesas": df,
        "transferencias_por_tipo": [],
        "orcamento": {"dotacao": 0, "empenhado": 0, "taxa_execucao": 0},
    }
