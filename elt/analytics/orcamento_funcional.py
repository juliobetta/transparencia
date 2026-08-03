import pandas as pd
from sqlalchemy import text


def get_orcamento_funcional(conn, year: int, empresa_ids: list[str] | None = None) -> pd.DataFrame:
    empresa_clause = "AND empresa_id = ANY(:empresas)" if empresa_ids else ""
    params: dict = {"ano": year}
    if empresa_ids:
        params["empresas"] = empresa_ids
    query = text(f"""
        SELECT funcao_nome, dotacao_atualizada, subfuncao_nome, empenhado, liquidado, pago
        FROM fct_despesas
        WHERE ano = :ano AND funcao_nome IS NOT NULL {empresa_clause}
    """)
    df = pd.read_sql_query(query, conn, params=params)

    # Converte colunas monetárias em texto para numérico
    for col in ["dotacao_atualizada", "empenhado", "liquidado", "pago"]:
        df[col] = pd.to_numeric(df[col].astype(str).str.replace(",", "."), errors="coerce").fillna(0)

    return df.groupby(["funcao_nome", "subfuncao_nome"], as_index=False).agg(
        dotacao_atualizada=("dotacao_atualizada", "sum"),
        empenhado=("empenhado", "sum"),
        liquidado=("liquidado", "sum"),
        pago=("pago", "sum"),
    )
