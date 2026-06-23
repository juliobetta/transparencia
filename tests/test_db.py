import sqlite3
import pytest
import db


@pytest.fixture
def conn():
    c = sqlite3.connect(":memory:")
    c.row_factory = sqlite3.Row
    db.create_tables(c)
    yield c
    c.close()


def test_create_tables_creates_despesas_por_orgao(conn):
    cur = conn.execute("SELECT name FROM sqlite_master WHERE type='table'")
    tables = {r["name"] for r in cur.fetchall()}
    assert "despesas_por_orgao" in tables
    assert "licitacoes" in tables
    assert "pessoal" in tables


def test_upsert_inserts_rows(conn):
    rows = [
        {"ano": 2025, "empresa": "7", "codigo": "01", "descricao": "SAUDE",
         "empenhado": "1000", "liquidado": "900", "pago": "800",
         "dotac": "2000", "altdo": "0", "dotacao_atualizada": "2000"},
    ]
    count = db.upsert(conn, "despesas_por_orgao", rows, key_cols=["ano", "empresa", "codigo"])
    assert count == 1
    cur = conn.execute("SELECT * FROM despesas_por_orgao")
    assert cur.fetchone()["descricao"] == "SAUDE"


def test_upsert_replaces_on_conflict(conn):
    row = {"ano": 2025, "empresa": "7", "codigo": "01", "descricao": "SAUDE",
           "empenhado": "1000", "liquidado": "900", "pago": "800",
           "dotac": "2000", "altdo": "0", "dotacao_atualizada": "2000"}
    db.upsert(conn, "despesas_por_orgao", [row], key_cols=["ano", "empresa", "codigo"])
    row["empenhado"] = "1500"
    db.upsert(conn, "despesas_por_orgao", [row], key_cols=["ano", "empresa", "codigo"])
    cur = conn.execute("SELECT empenhado FROM despesas_por_orgao WHERE codigo='01'")
    assert cur.fetchone()["empenhado"] == "1500"
    assert conn.execute("SELECT COUNT(*) FROM despesas_por_orgao").fetchone()[0] == 1
