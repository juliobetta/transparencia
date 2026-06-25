import sqlite3

import pandas as pd

DISPENSATION_THRESHOLD = 57_000  # Lei 14.133/2021 — limite para dispensa em serviços (valor conservador)
SAUDE_EMPRESA = "2"


def run(conn: sqlite3.Connection, year: int) -> pd.DataFrame:
    df = pd.read_sql_query(
        "SELECT ano, empresa, numero, fornecedor, objeto, valor, licitacao_numero, mes FROM contratos WHERE ano = ?",
        conn,
        params=(year,),
    )
    # keep only contracts with no linked licitação
    df = df[df["licitacao_numero"].fillna("").str.strip() == ""].copy()
    df["valor_num"] = pd.to_numeric(df["valor"].str.replace(",", "."), errors="coerce").fillna(0)
    df["acima_limite"] = df["valor_num"] > DISPENSATION_THRESHOLD
    df["orgao_saude"] = df["empresa"] == SAUDE_EMPRESA
    return df.drop(columns=["valor_num"])
