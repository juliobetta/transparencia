import pandas as pd
from sqlalchemy import text


def get_orcamento_funcional(conn, year: int, empresa_ids: list[str] | None = None) -> pd.DataFrame:
    empresa_clause = "AND empresa = ANY(:empresas)" if empresa_ids else ""
    params: dict = {"ano": year}
    if empresa_ids:
        params["empresas"] = empresa_ids
    query = text(f"""
        SELECT funcaonome, dotacatualizada, subfuncaonome, empenhado, liquidado, pago
        FROM despesas_gerais
        WHERE ano = :ano AND funcaonome IS NOT NULL {empresa_clause}
    """)
    df = pd.read_sql_query(query, conn, params=params)

    # Converte colunas monetárias em texto para numérico
    for col in ["dotacatualizada", "empenhado", "liquidado", "pago"]:
        df[col] = pd.to_numeric(df[col].str.replace(",", "."), errors="coerce").fillna(0)

    return df.groupby(["funcaonome", "subfuncaonome"], as_index=False).agg(
        dotacao_atualizada=("dotacatualizada", "sum"),
        empenhado=("empenhado", "sum"),
        liquidado=("liquidado", "sum"),
        pago=("pago", "sum"),
    )
