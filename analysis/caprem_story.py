import sqlite3


def run(_conn: sqlite3.Connection, _year: int):
    # Initial implementation: Fetch basic CAPREM metrics
    return {"total_transfers": 0, "transfers_by_type": [], "budget": {"dotacao": 0, "empenhado": 0, "taxa_execucao": 0}}
