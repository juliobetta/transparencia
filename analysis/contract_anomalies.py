import sqlite3

import pandas as pd

THRESHOLD = 57_000
NEAR_THRESHOLD_PCT = 0.20


def run(conn: sqlite3.Connection, year: int) -> dict:
    contratos = pd.read_sql_query(
        "SELECT empresa, numero, fornecedor, objeto, valor, licitacao_numero FROM contratos WHERE ano = ?",
        conn,
        params=(year,),
    )
    contratos["valor_num"] = pd.to_numeric(contratos["valor"].str.replace(",", "."), errors="coerce").fillna(0)

    # splitting: same supplier, ≥3 contracts, values within 20% below threshold
    lower = THRESHOLD * (1 - NEAR_THRESHOLD_PCT)
    near = contratos[(contratos["valor_num"] >= lower) & (contratos["valor_num"] < THRESHOLD)]
    supplier_counts = near.groupby("fornecedor").size()
    splitting = contratos[contratos["fornecedor"].isin(supplier_counts[supplier_counts >= 3].index)].copy()

    # repeated supplier: >50% of contracts in a department from one supplier
    dept_totals = contratos.groupby("empresa").size().rename("total")
    dept_supplier = contratos.groupby(["empresa", "fornecedor"]).size().rename("count").reset_index()
    dept_supplier = dept_supplier.join(dept_totals, on="empresa")
    dept_supplier["pct"] = dept_supplier["count"] / dept_supplier["total"]
    repeated_supplier = dept_supplier[dept_supplier["pct"] > 0.5].copy()

    # short window: licitações with data_abertura within 5 days of another in same year
    licitacoes = pd.read_sql_query(
        "SELECT numero, modalidade, objeto, data_abertura FROM licitacoes WHERE ano = ?", conn, params=(year,)
    )
    short_window = pd.DataFrame()
    if not licitacoes.empty and "data_abertura" in licitacoes.columns:
        licitacoes["data_abertura"] = pd.to_datetime(licitacoes["data_abertura"], errors="coerce")
        licitacoes = licitacoes.sort_values("data_abertura")
        licitacoes["dias_desde_anterior"] = licitacoes["data_abertura"].diff().dt.days
        short_window = licitacoes[licitacoes["dias_desde_anterior"] < 5].copy()

    return {"splitting": splitting, "repeated_supplier": repeated_supplier, "short_window": short_window}
