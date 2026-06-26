from typing import Any

import pandas as pd
from sqlalchemy import text


def _sum_column(conn: Any, table: str, col: str, year: int) -> float:
    try:
        df = pd.read_sql_query(text(f"SELECT {col} FROM {table} WHERE ano = :ano"), conn, params={"ano": year})
        if df.empty:
            return 0.0
        return float(pd.to_numeric(df[col].astype(str).str.replace(",", "."), errors="coerce").fillna(0).sum())
    except Exception:
        return 0.0


def run(conn: Any, years: list[int]) -> pd.DataFrame:
    records = []
    for year in years:
        propria_previsto = _sum_column(conn, "receita_orcamentaria", "previsao_atualizada", year)
        propria_arrecadado = _sum_column(conn, "receita_orcamentaria", "arrecadado_total", year)
        if propria_arrecadado == 0:
            propria_arrecadado = _sum_column(conn, "receita_orcamentaria", "arrecadado", year)

        uniao_previsto = _sum_column(conn, "receita_uniao", "previsao_atualizada", year)
        uniao_arrecadado = _sum_column(conn, "receita_uniao", "arrecadado_total", year)
        if uniao_arrecadado == 0:
            uniao_arrecadado = _sum_column(conn, "receita_uniao", "arrecadado", year)

        estado_previsto = _sum_column(conn, "receita_estado", "previsao_atualizada", year)
        estado_arrecadado = _sum_column(conn, "receita_estado", "arrecadado_total", year)
        if estado_arrecadado == 0:
            estado_arrecadado = _sum_column(conn, "receita_estado", "arrecadado", year)

        total_previsto = propria_previsto + uniao_previsto + estado_previsto
        total_arrecadado = propria_arrecadado + uniao_arrecadado + estado_arrecadado

        propria_compat = propria_arrecadado if (propria_arrecadado > 0 or year == 2026) else propria_previsto
        uniao_compat = uniao_arrecadado if (uniao_arrecadado > 0 or year == 2026) else uniao_previsto
        estado_compat = estado_arrecadado if (estado_arrecadado > 0 or year == 2026) else estado_previsto
        total_compat = propria_compat + uniao_compat + estado_compat
        pct = propria_compat / total_compat * 100 if total_compat > 0 else 0

        records.append(
            {
                "ano": year,
                "receita_propria": propria_compat,
                "transferencias_uniao": uniao_compat,
                "transferencias_estado": estado_compat,
                "total": total_compat,
                "pct_propria": pct,
                "alerta_dependencia": bool(pct < 10),
                "receita_propria_previsto": propria_previsto,
                "receita_propria_arrecadado": propria_arrecadado,
                "transferencias_uniao_previsto": uniao_previsto,
                "transferencias_uniao_arrecadado": uniao_arrecadado,
                "transferencias_estado_previsto": estado_previsto,
                "transferencias_estado_arrecadado": estado_arrecadado,
                "total_previsto": total_previsto,
                "total_arrecadado": total_arrecadado,
            }
        )
    df = pd.DataFrame(records)
    df["alerta_dependencia"] = df["alerta_dependencia"].astype(object)
    return df
