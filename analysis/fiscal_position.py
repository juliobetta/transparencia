import re
from typing import Any

import pandas as pd
from sqlalchemy import text

from analysis import revenue_sources


def _sanitize_descricao(s: str) -> str:
    s = s.strip()
    # Remove leading document-number prefix (e.g. "03.163.892 NOME" → "NOME")
    s = re.sub(r"^\d{2}\.\d{3}\.\d{3}\s+", "", s)
    return s


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
    restos_pendentes_total = sum(float(r["pendente"]) for r in restos_pendentes)
    # Only pre-2025 obligations represent inherited debt from the previous administration
    restos_pendentes_anteriores = sum(float(r["pendente"]) for r in restos_pendentes if int(r["ano"]) < 2025)

    # 5. Top 5 creditors with pending restos from current administration (2025+)
    top_credores_adm_atual = []
    try:
        df_cred = pd.read_sql_query(
            text("SELECT descricao, empenhado, pago FROM despesas_restos_pagar WHERE ano >= 2025"),
            conn,
        )
        df_cred["emp_f"] = pd.to_numeric(
            df_cred["empenhado"].astype(str).str.replace(",", "."), errors="coerce"
        ).fillna(0)
        df_cred["pago_f"] = pd.to_numeric(df_cred["pago"].astype(str).str.replace(",", "."), errors="coerce").fillna(0)
        df_cred["pendente"] = df_cred["emp_f"] - df_cred["pago_f"]
        df_cred["descricao"] = df_cred["descricao"].fillna("Sem identificação")
        top = (
            df_cred.groupby("descricao")["pendente"]
            .sum()
            .reset_index()
            .sort_values("pendente", ascending=False)
            .head(5)
        )
        top_credores_adm_atual = top.rename(columns={"descricao": "Fornecedor", "pendente": "Pendente"}).to_dict(
            "records"
        )
    except Exception:
        pass

    return {
        "total_arrecadado": total_arrecadado,
        "despesas_pagas": despesas_pagas,
        "restos_pagos_no_ano": restos_pagos_no_ano,
        "total_saidas": total_saidas,
        "saldo_estimado": saldo_estimado,
        "restos_pendentes": restos_pendentes,
        "restos_pendentes_total": restos_pendentes_total,
        "restos_pendentes_anteriores": restos_pendentes_anteriores,
        "top_credores_adm_atual": top_credores_adm_atual,
    }


def get_unpaid_suppliers(conn: Any, year: int | None = None) -> pd.DataFrame:
    try:
        df = pd.read_sql_query(
            text("SELECT descricao, ano, empenhado, pago FROM despesas_restos_pagar"),
            conn,
        )
    except Exception:
        return pd.DataFrame()

    if year is not None:
        df = df[df["ano"] <= year]

    df["emp_f"] = pd.to_numeric(df["empenhado"].astype(str).str.replace(",", "."), errors="coerce").fillna(0)
    df["pago_f"] = pd.to_numeric(df["pago"].astype(str).str.replace(",", "."), errors="coerce").fillna(0)
    df["pendente"] = df["emp_f"] - df["pago_f"]
    df = df[(df["emp_f"] > 0) & (df["pendente"] > 0)].copy()
    df["descricao"] = df["descricao"].fillna("Sem identificação").apply(_sanitize_descricao)

    return (
        df.groupby("descricao")
        .agg(
            aguardando_desde=("ano", "min"),
            num_registros=("ano", "count"),
            total_empenhado=("emp_f", "sum"),
            total_pago=("pago_f", "sum"),
            pendente=("pendente", "sum"),
        )
        .reset_index()
        .sort_values("pendente", ascending=False)
    )


def get_low_value_restos(conn: Any, threshold: float = 10.0) -> pd.DataFrame:
    try:
        df = pd.read_sql_query(
            text("SELECT descricao, fornecedor, ano, numero, empenhado, pago FROM despesas_restos_pagar"),
            conn,
        )
    except Exception:
        return pd.DataFrame()

    df["emp_f"] = pd.to_numeric(df["empenhado"].astype(str).str.replace(",", "."), errors="coerce").fillna(0)
    df["pago_f"] = pd.to_numeric(df["pago"].astype(str).str.replace(",", "."), errors="coerce").fillna(0)
    return (
        df[(df["emp_f"] > 0) & (df["emp_f"] < threshold)]
        .assign(descricao=df["descricao"].fillna("Sem identificação").apply(_sanitize_descricao))[
            ["ano", "numero", "descricao", "fornecedor", "emp_f", "pago_f"]
        ]
        .rename(
            columns={
                "ano": "Ano",
                "numero": "Nº",
                "descricao": "Descrição",
                "fornecedor": "Fornecedor",
                "emp_f": "Empenhado",
                "pago_f": "Pago",
            }
        )
        .sort_values("Empenhado")
    )
