import re
from typing import Any

import pandas as pd
from sqlalchemy import text

from analysis import revenue_sources


def _sanitize_descricao(s: str) -> str:
    s = s.strip()
    # Remove prefixo de número de documento (ex: "03.163.892 NOME" → "NOME")
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
    # 1. Total receitas arrecadadas (reutiliza lógica de raiz existente)
    rev_df = revenue_sources.run(conn, [year])
    total_arrecadado = float(rev_df.iloc[0]["total_arrecadado"]) if not rev_df.empty else 0.0

    # 2. Despesas correntes pagas no ano
    despesas_pagas = _sum_varchar_col(conn, "despesas_por_orgao", "pago", year)

    # 3. Soma do pago de restos cujo exercício corresponde ao ano informado
    restos_pagos_no_ano = _sum_varchar_col(conn, "despesas_restos_pagar", "pago", year)

    # 4. Restos pendentes por exercício
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
    # Apenas obrigações pré-2025 representam dívida herdada da gestão anterior
    restos_pendentes_anteriores = sum(float(r["pendente"]) for r in restos_pendentes if int(r["ano"]) < 2025)

    # 5. Top 5 credores com restos pendentes da administração atual (2025+)
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
        "saldo_apos_restos": saldo_estimado - restos_pendentes_total,
        "restos_pendentes": restos_pendentes,
        "restos_pendentes_total": restos_pendentes_total,
        "restos_pendentes_anteriores": restos_pendentes_anteriores,
        "top_credores_adm_atual": top_credores_adm_atual,
    }


def get_fornecedores_pendentes(conn: Any, year: int | None = None) -> pd.DataFrame:
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
    df["descricao"] = df["descricao"].fillna("Sem identificação").apply(_sanitize_descricao)

    # Filtra APÓS groupby para que cancelamentos (emp_f negativo) reduzam o saldo líquido corretamente
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
        .query("pendente > 0")
        .sort_values("pendente", ascending=False)
    )


def get_tendencia_fornecedores_pendentes(conn: Any, years: list[int]) -> pd.DataFrame:
    try:
        df = pd.read_sql_query(
            text("SELECT ano, descricao, empenhado, pago FROM despesas_restos_pagar"),
            conn,
        )
    except Exception:
        return pd.DataFrame()

    df["emp_f"] = pd.to_numeric(df["empenhado"].astype(str).str.replace(",", "."), errors="coerce").fillna(0)
    df["pago_f"] = pd.to_numeric(df["pago"].astype(str).str.replace(",", "."), errors="coerce").fillna(0)
    df["pendente"] = df["emp_f"] - df["pago_f"]
    # Mantém todos os registros incluindo cancelamentos (emp_f < 0) para reduzir corretamente os totais do snapshot

    rows = []
    for year in years:
        snapshot = df[df["ano"] <= year]
        rows.append(
            {
                "ano": year,
                "total_pendente": float(snapshot["pendente"].sum()),
                "num_fornecedores": int(snapshot["descricao"].nunique()),
            }
        )
    return pd.DataFrame(rows)


def resumo_pendentes(df: pd.DataFrame) -> dict:
    return {
        "total": float(df["pendente"].sum()),
        "count": len(df),
        "oldest": int(df["aguardando_desde"].min()) if not df.empty else 0,
    }


def piechart_pendentes(df: pd.DataFrame, n: int = 10) -> pd.DataFrame:
    top = df.head(n)
    outros = float(df["pendente"].sum()) - float(top["pendente"].sum())
    slices = top[["descricao", "pendente"]].rename(columns={"descricao": "Fornecedor", "pendente": "Pendente"})
    if outros > 0:
        slices = pd.concat([slices, pd.DataFrame({"Fornecedor": ["Outros"], "Pendente": [outros]})])
    return slices


def get_pendentes_por_exercicio(conn: Any) -> pd.DataFrame:
    """Retorna totais de RAP pendentes por exercício (para exibição por seção)."""
    try:
        df = pd.read_sql_query(
            text("SELECT ano, empenhado, pago FROM despesas_restos_pagar"),
            conn,
        )
    except Exception:
        return pd.DataFrame()

    df["emp_f"] = pd.to_numeric(df["empenhado"].astype(str).str.replace(",", "."), errors="coerce").fillna(0)
    df["pago_f"] = pd.to_numeric(df["pago"].astype(str).str.replace(",", "."), errors="coerce").fillna(0)
    df["pendente"] = df["emp_f"] - df["pago_f"]
    return (
        df.groupby("ano")
        .agg(total_empenhado=("emp_f", "sum"), total_pago=("pago_f", "sum"), total_pendente=("pendente", "sum"))
        .reset_index()
        .query("total_pendente > 0")
        .sort_values("ano")
        .rename(
            columns={
                "ano": "Exercício",
                "total_empenhado": "Empenhado",
                "total_pago": "Pago",
                "total_pendente": "Pendente",
            }
        )
    )


def get_restos_baixo_valor(conn: Any, year: int | None = None, threshold: float = 10.0) -> pd.DataFrame:
    try:
        df = pd.read_sql_query(
            text("SELECT descricao, ano, numero, empenhado, pago FROM despesas_restos_pagar"),
            conn,
        )
    except Exception:
        return pd.DataFrame()

    df["emp_f"] = pd.to_numeric(df["empenhado"].astype(str).str.replace(",", "."), errors="coerce").fillna(0)
    df["pago_f"] = pd.to_numeric(df["pago"].astype(str).str.replace(",", "."), errors="coerce").fillna(0)
    if year is not None:
        df = df[df["ano"] <= year]
    return (
        df[(df["emp_f"] > 0) & (df["emp_f"] < threshold)]
        .assign(descricao=df["descricao"].fillna("Sem identificação").apply(_sanitize_descricao))[
            ["ano", "numero", "descricao", "emp_f", "pago_f"]
        ]
        .rename(
            columns={
                "ano": "Ano",
                "numero": "Nº",
                "descricao": "Descrição",
                "emp_f": "Empenhado",
                "pago_f": "Pago",
            }
        )
        .sort_values("Empenhado")
    )
