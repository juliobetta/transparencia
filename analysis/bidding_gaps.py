from typing import Any

import pandas as pd
from sqlalchemy import text

DISPENSATION_THRESHOLD = 62_725.59
SAUDE_EMPRESA = "2"


def counts_by_year(conn: Any, years: list[int]) -> dict[int, int]:
    """Return {year: count_above_limit} in a single query instead of N round-trips."""
    placeholders = ", ".join(str(y) for y in years)
    df = pd.read_sql_query(
        text(f"SELECT ano, licitacao_numero, valcon FROM contratos WHERE ano IN ({placeholders})"),
        conn,
    )
    df = df[df["licitacao_numero"].fillna("").str.strip() == ""].copy()
    df["valor_num"] = pd.to_numeric(df["valcon"].astype(str).str.replace(",", "."), errors="coerce").fillna(0)
    df["acima_limite"] = df["valor_num"] > DISPENSATION_THRESHOLD
    counts = df.groupby("ano")["acima_limite"].sum().astype(int)
    return {y: int(counts.get(y, 0)) for y in years}


def run(conn: Any, year: int) -> pd.DataFrame:
    df = pd.read_sql_query(
        text(
            "SELECT ano, empresa, numero, fornecedor, objeto, valcon, licitacao_numero, mes FROM contratos WHERE ano = :ano"
        ),
        conn,
        params={"ano": year},
    )
    df = df[df["licitacao_numero"].fillna("").str.strip() == ""].copy()
    df["valor_num"] = pd.to_numeric(df["valcon"].astype(str).str.replace(",", "."), errors="coerce").fillna(0)
    df["acima_limite"] = df["valor_num"] > DISPENSATION_THRESHOLD
    df["orgao_saude"] = df["empresa"] == SAUDE_EMPRESA
    return df.drop(columns=["valor_num"])
