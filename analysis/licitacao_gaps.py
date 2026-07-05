from typing import Any

import pandas as pd
from sqlalchemy import text

from analysis.constants import dispensation_threshold

SAUDE_EMPRESA = "2"


def counts_by_year(conn: Any, years: list[int]) -> dict[int, int]:
    """Retorna {ano: contagem_acima_do_limite} usando o limite aplicável por contrato."""
    placeholders = ", ".join(str(y) for y in years)
    df = pd.read_sql_query(
        text(
            f"SELECT ano, licitacao_numero, valcon, numobra, tipocoobra, objeto"
            f" FROM contratos WHERE ano IN ({placeholders})"
        ),
        conn,
    )
    df = df[df["licitacao_numero"].fillna("").str.strip() == ""].copy()
    df["valor_num"] = pd.to_numeric(df["valcon"].astype(str).str.replace(",", "."), errors="coerce").fillna(0)
    df["threshold"] = df.apply(
        lambda r: dispensation_threshold(r.get("numobra"), r.get("tipocoobra"), r.get("objeto")), axis=1
    )
    df["acima_limite"] = df["valor_num"] > df["threshold"]
    counts = df.groupby("ano")["acima_limite"].sum().astype(int)
    return {y: int(counts.get(y, 0)) for y in years}


def totals_sem_licitacao_por_ano(conn: Any, years: list[int]) -> dict[int, int]:
    """Retorna {ano: total_contratos_sem_licitacao} para todos os valores (acima e abaixo do limite)."""
    placeholders = ", ".join(str(y) for y in years)
    df = pd.read_sql_query(
        text(f"SELECT ano, licitacao_numero FROM contratos WHERE ano IN ({placeholders})"),
        conn,
    )
    df = df[df["licitacao_numero"].fillna("").str.strip() == ""]
    counts = df.groupby("ano").size()
    return {y: int(counts.get(y, 0)) for y in years}


def run(conn: Any, year: int) -> pd.DataFrame:
    df = pd.read_sql_query(
        text(
            "SELECT ano, empresa, numero, fornecedor, objeto, valcon, licitacao_numero, mes,"
            " numobra, tipocoobra"
            " FROM contratos WHERE ano = :ano"
        ),
        conn,
        params={"ano": year},
    )
    df = df[df["licitacao_numero"].fillna("").str.strip() == ""].copy()
    df["valor_num"] = pd.to_numeric(df["valcon"].astype(str).str.replace(",", "."), errors="coerce").fillna(0)
    df["threshold"] = df.apply(
        lambda r: dispensation_threshold(r.get("numobra"), r.get("tipocoobra"), r.get("objeto")), axis=1
    )
    df["acima_limite"] = df["valor_num"] > df["threshold"]
    df["orgao_saude"] = df["empresa"] == SAUDE_EMPRESA
    df["periodo"] = df["mes"].astype(str).str.zfill(2) + "/" + df["ano"].astype(str)
    return df.drop(columns=["valor_num", "threshold"])


def filter_above_limit(df: pd.DataFrame) -> pd.DataFrame:
    return df[df["acima_limite"]]


def filter_above_limit_health(df: pd.DataFrame) -> pd.DataFrame:
    return df[df["acima_limite"] & df["orgao_saude"]]
