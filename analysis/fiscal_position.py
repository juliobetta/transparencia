from typing import Any

import pandas as pd
from sqlalchemy import text

from analysis import revenue_sources


def _sum_varchar_col(conn: Any, table: str, col: str, year: int) -> float:
    try:
        df = pd.read_sql_query(
            text(f"SELECT {col} FROM {table} WHERE ano = :ano"),
            conn,
            params={"ano": year},
        )
        if df.empty:
            return 0.0
        return float(pd.to_numeric(df[col].astype(str).str.replace(",", "."), errors="coerce").fillna(0).sum())
    except Exception:
        return 0.0


def run(conn: Any, year: int) -> dict:
    # 1. Total receitas arrecadadas (reuses existing root-only logic)
    rev_df = revenue_sources.run(conn, [year])
    total_arrecadado = float(rev_df.iloc[0]["total_arrecadado"]) if not rev_df.empty else 0.0

    # 2. Current-year budget paid
    despesas_pagas = _sum_varchar_col(conn, "despesas_por_orgao", "pago", year)

    # 3. Sum of pago for restos whose exercise year matches the given year
    restos_pagos_no_ano = _sum_varchar_col(conn, "despesas_restos_pagar", "pago", year)

    # 4. Outstanding restos by exercise year
    restos_pendentes = []
    try:
        df = pd.read_sql_query(
            text("SELECT ano, empenhado, pago FROM despesas_restos_pagar ORDER BY ano"),
            conn,
        )
        df["emp_f"] = pd.to_numeric(df["empenhado"].astype(str).str.replace(",", "."), errors="coerce").fillna(0)
        df["pago_f"] = pd.to_numeric(df["pago"].astype(str).str.replace(",", "."), errors="coerce").fillna(0)
        grouped = df.groupby("ano").agg(empenhado=("emp_f", "sum"), pago=("pago_f", "sum")).reset_index()
        for _, row in grouped.iterrows():
            ano = int(row["ano"])
            emp = float(row["empenhado"])
            pag = float(row["pago"])
            restos_pendentes.append(
                {
                    "ano": ano,
                    "administracao": "Adm. Anterior" if ano < 2025 else "Adm. Atual",
                    "empenhado": emp,
                    "pago": pag,
                    "pendente": emp - pag,
                }
            )
    except Exception:
        pass

    total_saidas = despesas_pagas + restos_pagos_no_ano
    saldo_estimado = total_arrecadado - total_saidas
    restos_pendentes_total = sum(float(r["pendente"]) for r in restos_pendentes if int(r["ano"]) == year)
    # Only pre-2025 obligations represent inherited debt from the previous administration
    restos_pendentes_anteriores = sum(float(r["pendente"]) for r in restos_pendentes if int(r["ano"]) < 2025)

    return {
        "total_arrecadado": total_arrecadado,
        "despesas_pagas": despesas_pagas,
        "restos_pagos_no_ano": restos_pagos_no_ano,
        "total_saidas": total_saidas,
        "saldo_estimado": saldo_estimado,
        "restos_pendentes": restos_pendentes,
        "restos_pendentes_total": restos_pendentes_total,
        "restos_pendentes_anteriores": restos_pendentes_anteriores,
    }
