import sqlite3

import pandas as pd

CAPREM_EMPRESA_IDS = ["2", "3", "7", "8", "9", "10"]

def run(conn: sqlite3.Connection, year: int):
    # Fetch CAPREM expenses using a tuple of IDs
    placeholders = ",".join("?" for _ in CAPREM_EMPRESA_IDS)
    df = pd.read_sql_query(
        f"SELECT * FROM despesas_por_fornecedor WHERE empresa IN ({placeholders}) AND ano = ?",
        conn,
        params=(*CAPREM_EMPRESA_IDS, year),
    )

    if not df.empty:
        # Convert numeric columns
        for col in ["empenhado", "liquidado", "pago"]:
            df[col] = pd.to_numeric(df[col].str.replace(",", "."), errors="coerce").fillna(0)

        total_transfers = df["empenhado"].sum()
        count_operations = len(df)
    else:
        total_transfers = 0
        count_operations = 0

    return {
        "total_transfers": total_transfers,
        "count_operations": count_operations,
        "despesas": df,
        "transfers_by_type": [],
        "budget": {"dotacao": 0, "empenhado": 0, "taxa_execucao": 0},
    }
