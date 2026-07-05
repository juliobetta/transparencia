import pandas as pd
from sqlalchemy import text


def get_orcamento_funcional(conn, year: int) -> pd.DataFrame:
    query = text("""
        SELECT funcaonome, dotacatualizada, subfuncaonome, empenhado, liquidado, pago
        FROM despesas_gerais
        WHERE ano = :ano AND funcaonome IS NOT NULL
    """)
    df = pd.read_sql_query(query, conn, params={"ano": year})

    # Converte colunas monetárias em texto para numérico
    for col in ["dotacatualizada", "empenhado", "liquidado", "pago"]:
        df[col] = pd.to_numeric(df[col].str.replace(",", "."), errors="coerce").fillna(0)

    return df.groupby(["funcaonome", "subfuncaonome"], as_index=False).agg(
        dotacao_atualizada=("dotacatualizada", "sum"),
        empenhado=("empenhado", "sum"),
        liquidado=("liquidado", "sum"),
        pago=("pago", "sum"),
    )
