from typing import Any

import pandas as pd
from sqlalchemy import text

CAPREM_CODE = "1061"


def _to_float(series: pd.Series) -> pd.Series:
    return pd.to_numeric(series.astype(str).str.replace(",", "."), errors="coerce").fillna(0)


def _entity_breakdown(conn: Any, year: int) -> pd.DataFrame:
    df = pd.read_sql_query(
        text("""
            SELECT e.nome AS entidade, f.empresa, f.empenhado, f.liquidado, f.pago
            FROM despesas_por_fornecedor f
            JOIN empresas e ON e.id::text = f.empresa
            WHERE f.codigo = :codigo AND f.ano = :ano
            ORDER BY CAST(NULLIF(REPLACE(f.empenhado, ',', '.'), '') AS FLOAT) DESC NULLS LAST
        """),
        conn,
        params={"codigo": CAPREM_CODE, "ano": year},
    )
    for col in ["empenhado", "liquidado", "pago"]:
        df[col] = _to_float(df[col])
    return df


def _annual_trend(conn: Any) -> pd.DataFrame:
    df = pd.read_sql_query(
        text("""
            SELECT ano,
                   SUM(CAST(NULLIF(REPLACE(empenhado, ',', '.'), '') AS FLOAT)) AS empenhado,
                   SUM(CAST(NULLIF(REPLACE(liquidado, ',', '.'), '') AS FLOAT)) AS liquidado,
                   SUM(CAST(NULLIF(REPLACE(pago, ',', '.'), '') AS FLOAT)) AS pago
            FROM despesas_por_fornecedor
            WHERE codigo = :codigo
            GROUP BY ano ORDER BY ano
        """),
        conn,
        params={"codigo": CAPREM_CODE},
    )
    for col in ["empenhado", "liquidado", "pago"]:
        df[col] = _to_float(df[col])
    return df


def _function_breakdown(conn: Any, year: int) -> pd.DataFrame:
    df = pd.read_sql_query(
        text("""
            SELECT funcaonome, subfuncaonome,
                   SUM(CAST(NULLIF(REPLACE(empenhado, ',', '.'), '') AS FLOAT)) AS empenhado,
                   SUM(CAST(NULLIF(REPLACE(pago, ',', '.'), '') AS FLOAT)) AS pago
            FROM despesas_gerais
            WHERE nomefor ILIKE '%CAPREM%' AND ano = :ano AND tpem != 'AN'
            GROUP BY funcaonome, subfuncaonome
            ORDER BY empenhado DESC
        """),
        conn,
        params={"ano": year},
    )
    for col in ["empenhado", "pago"]:
        df[col] = _to_float(df[col])
    return df


def _monthly_trend(conn: Any, year: int) -> pd.DataFrame:
    df = pd.read_sql_query(
        text("""
            SELECT mes,
                   SUM(CAST(NULLIF(REPLACE(empenhado, ',', '.'), '') AS FLOAT)) AS empenhado,
                   SUM(CAST(NULLIF(REPLACE(pago, ',', '.'), '') AS FLOAT)) AS pago
            FROM despesas_gerais
            WHERE nomefor ILIKE '%CAPREM%' AND ano = :ano AND tpem != 'AN'
            GROUP BY mes ORDER BY mes
        """),
        conn,
        params={"ano": year},
    )
    for col in ["empenhado", "pago"]:
        df[col] = _to_float(df[col])
    return df


_ELEMENTO_LABELS: dict[str, str] = {
    "13": "Contribuições Patronais (RPPS/INSS)",
    "46": "Auxílio-Alimentação",
    "71": "Principal da Dívida Contratual Resgatado",
    "91": "Sentenças Judiciais",
    "97": "Aporte para Cobertura do Déficit Atuarial do RPPS",
}


def _nature_breakdown(conn: Any, year: int) -> pd.DataFrame:
    df = pd.read_sql_query(
        text("""
            SELECT elemento, natureza,
                   SUM(CAST(NULLIF(REPLACE(empenhado, ',', '.'), '') AS FLOAT)) AS empenhado
            FROM despesas_gerais
            WHERE nomefor ILIKE '%CAPREM%' AND ano = :ano AND tpem != 'AN'
            GROUP BY elemento, natureza
            ORDER BY empenhado DESC
        """),
        conn,
        params={"ano": year},
    )
    df["empenhado"] = _to_float(df["empenhado"])
    df["descricao"] = df["elemento"].astype(str).map(_ELEMENTO_LABELS).fillna("Elemento " + df["elemento"].astype(str))
    return df


def run(conn: Any, year: int) -> dict:
    df = pd.read_sql_query(
        text("SELECT * FROM despesas_por_fornecedor WHERE codigo = :codigo AND ano = :ano"),
        conn,
        params={"codigo": CAPREM_CODE, "ano": year},
    )

    if not df.empty:
        for col in ["empenhado", "liquidado", "pago"]:
            df[col] = _to_float(df[col])
        total_transferencias = float(df["empenhado"].sum())
        total_liquidado = float(df["liquidado"].sum())
        total_pago = float(df["pago"].sum())
        count_operacoes = len(df)
    else:
        total_transferencias = 0.0
        total_liquidado = 0.0
        total_pago = 0.0
        count_operacoes = 0

    taxa_execucao = total_pago / total_transferencias if total_transferencias > 0 else 0.0

    return {
        "total_transferencias": total_transferencias,
        "total_liquidado": total_liquidado,
        "total_pago": total_pago,
        "taxa_execucao": taxa_execucao,
        "count_operacoes": count_operacoes,
        "despesas": df,
        "entidades": _entity_breakdown(conn, year),
        "tendencia_anual": _annual_trend(conn),
        "funcoes": _function_breakdown(conn, year),
        "mensal": _monthly_trend(conn, year),
        "natureza": _nature_breakdown(conn, year),
    }
