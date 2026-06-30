from typing import Any

import pandas as pd
from sqlalchemy import text

from analysis.constants import NEAR_THRESHOLD_PCT, dispensation_threshold


def splitting_counts_by_year(conn: Any, years: list[int]) -> dict[int, int]:
    placeholders = ", ".join(str(y) for y in years)
    df = pd.read_sql_query(
        text(
            f"SELECT ano, empresa, fornecedor, valcon, numobra, tipocoobra, objeto"
            f" FROM contratos WHERE ano IN ({placeholders})"
        ),
        conn,
    )
    df["valor_num"] = pd.to_numeric(df["valcon"].astype(str).str.replace(",", "."), errors="coerce").fillna(0)
    df["threshold"] = df.apply(
        lambda r: dispensation_threshold(r.get("numobra"), r.get("tipocoobra"), r.get("objeto")), axis=1
    )
    df["lower"] = df["threshold"] * (1 - NEAR_THRESHOLD_PCT)
    df["near"] = (df["valor_num"] >= df["lower"]) & (df["valor_num"] < df["threshold"])

    result = {}
    for y in years:
        near_y = df[(df["ano"] == y) & df["near"]]
        # Group by órgão executor + fornecedor (subelemento de despesa not available in contratos table)
        counts = near_y.groupby(["empresa", "fornecedor"]).size()
        result[y] = int((counts >= 3).sum())
    return result


def run(conn: Any, year: int) -> dict:
    contratos = pd.read_sql_query(
        text(
            "SELECT ano, empresa, numero, fornecedor, objeto, valcon, licitacao_numero, mes,"
            " numobra, tipocoobra"
            " FROM contratos WHERE ano = :ano"
        ),
        conn,
        params={"ano": year},
    )
    contratos["valor_num"] = pd.to_numeric(
        contratos["valcon"].astype(str).str.replace(",", "."), errors="coerce"
    ).fillna(0)
    contratos["threshold"] = contratos.apply(
        lambda r: dispensation_threshold(r.get("numobra"), r.get("tipocoobra"), r.get("objeto")), axis=1
    )
    contratos["lower"] = contratos["threshold"] * (1 - NEAR_THRESHOLD_PCT)
    near = contratos[(contratos["valor_num"] >= contratos["lower"]) & (contratos["valor_num"] < contratos["threshold"])]

    # Splitting: same órgão executor + same fornecedor with 3+ contracts just below their applicable limit
    # (subelemento de despesa would refine this further but is not available in the contratos table)
    supplier_counts = near.groupby(["empresa", "fornecedor"]).size()
    splitting_keys = supplier_counts[supplier_counts >= 3].index
    splitting = near[near.set_index(["empresa", "fornecedor"]).index.isin(splitting_keys)].copy()
    if not splitting.empty:
        splitting["Período"] = splitting["mes"].astype(str).str.zfill(2) + "/" + splitting["ano"].astype(str)

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
