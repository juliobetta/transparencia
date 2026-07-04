import pandas as pd
from sqlalchemy import text


def get_functional_budget(conn, year: int) -> pd.DataFrame:
    query = text("""
        SELECT funcaonome, subfuncaonome, empenhado, liquidado, pago
        FROM despesas_gerais
        WHERE ano = :ano AND funcaonome IS NOT NULL
    """)
    df = pd.read_sql_query(query, conn, params={"ano": year})

    # Convert string-based currency to numeric
    for col in ["empenhado", "liquidado", "pago"]:
        df[col] = pd.to_numeric(df[col].str.replace(",", "."), errors="coerce").fillna(0)

    return df.groupby(["funcaonome", "subfuncaonome"], as_index=False).agg(
        empenhado=("empenhado", "sum"), liquidado=("liquidado", "sum"), pago=("pago", "sum")
    )
