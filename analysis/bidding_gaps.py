from typing import Any

import pandas as pd
from sqlalchemy import text

DISPENSATION_THRESHOLD = 57_000
SAUDE_EMPRESA = "2"


def run(conn: Any, year: int) -> pd.DataFrame:
    df = pd.read_sql_query(
        text(
            "SELECT ano, empresa, numero, fornecedor, objeto, valor, licitacao_numero, mes FROM contratos WHERE ano = :ano"
        ),
        conn,
        params={"ano": year},
    )
    df = df[df["licitacao_numero"].fillna("").str.strip() == ""].copy()
    df["valor_num"] = pd.to_numeric(df["valor"].str.replace(",", "."), errors="coerce").fillna(0)
    df["acima_limite"] = df["valor_num"] > DISPENSATION_THRESHOLD
    df["orgao_saude"] = df["empresa"] == SAUDE_EMPRESA
    return df.drop(columns=["valor_num"])
