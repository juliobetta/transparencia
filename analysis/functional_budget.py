import pandas as pd
from sqlalchemy import text


def get_functional_budget(conn, year: int) -> pd.DataFrame:
    query = text("""
        SELECT funcaonome, subfuncaonome
               SUM(CAST(COALESCE(NULLIF(empenhado, ''), '0') AS FLOAT)) as empenhado,
               SUM(CAST(COALESCE(NULLIF(liquidado, ''), '0') AS FLOAT)) as liquidado,
               SUM(CAST(COALESCE(NULLIF(pago, ''), '0') AS FLOAT)) as pago
        FROM despesas_gerais
        WHERE ano = :ano AND funcaonome IS NOT NULL
        GROUP BY funcaonome, subfuncaonome
    """)
    return pd.read_sql_query(query, conn, params={"ano": year})
