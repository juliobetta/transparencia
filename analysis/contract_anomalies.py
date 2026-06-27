from typing import Any

import pandas as pd
from sqlalchemy import text

THRESHOLD = 62_725.59
NEAR_THRESHOLD_PCT = 0.20


def splitting_counts_by_year(conn: Any, years: list[int]) -> dict[int, int]:
    placeholders = ", ".join(str(y) for y in years)
    df = pd.read_sql_query(
        text(f"SELECT ano, fornecedor, valcon FROM contratos WHERE ano IN ({placeholders})"),
        conn,
    )
    df["valor_num"] = pd.to_numeric(df["valcon"].astype(str).str.replace(",", "."), errors="coerce").fillna(0)
    lower = THRESHOLD * (1 - NEAR_THRESHOLD_PCT)
    near = df[(df["valor_num"] >= lower) & (df["valor_num"] < THRESHOLD)]
    result = {}
    for y in years:
        near_y = near[near["ano"] == y]
        counts = near_y.groupby("fornecedor").size()
        result[y] = int((counts >= 3).sum())
    return result


def run(conn: Any, year: int) -> dict:
    contratos = pd.read_sql_query(
        text(
            "SELECT ano, empresa, numero, fornecedor, objeto, valcon, licitacao_numero, mes FROM contratos WHERE ano = :ano"
        ),
        conn,
        params={"ano": year},
    )
    contratos["valor_num"] = pd.to_numeric(
        contratos["valcon"].astype(str).str.replace(",", "."), errors="coerce"
    ).fillna(0)

    lower = THRESHOLD * (1 - NEAR_THRESHOLD_PCT)
    near = contratos[(contratos["valor_num"] >= lower) & (contratos["valor_num"] < THRESHOLD)]
    supplier_counts = near.groupby("fornecedor").size()
    splitting = near[near["fornecedor"].isin(supplier_counts[supplier_counts >= 3].index)].copy()

    dept_totals = contratos.groupby("empresa").size().rename("total")
    dept_supplier = contratos.groupby(["empresa", "fornecedor"]).size().rename("count").reset_index()
    dept_supplier = dept_supplier.join(dept_totals, on="empresa")
    dept_supplier["pct"] = dept_supplier["count"] / dept_supplier["total"]
    repeated_supplier = dept_supplier[dept_supplier["pct"] > 0.5].copy()

    licitacoes = pd.read_sql_query(
        text("SELECT numero, modalidade, objeto, data_abertura FROM licitacoes WHERE ano = :ano"),
        conn,
        params={"ano": year},
    )
    short_window = pd.DataFrame()
    if not licitacoes.empty and "data_abertura" in licitacoes.columns:
        licitacoes["data_abertura"] = pd.to_datetime(licitacoes["data_abertura"], errors="coerce")
        licitacoes = licitacoes.sort_values("data_abertura")
        licitacoes["dias_desde_anterior"] = licitacoes["data_abertura"].diff().dt.days
        short_window = licitacoes[licitacoes["dias_desde_anterior"] < 5].copy()

    return {"splitting": splitting, "repeated_supplier": repeated_supplier, "short_window": short_window}
