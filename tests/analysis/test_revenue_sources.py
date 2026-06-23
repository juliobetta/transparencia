import sqlite3

import pytest

import db
from analysis.revenue_sources import run


@pytest.fixture
def conn():
    c = sqlite3.connect(":memory:")
    c.row_factory = sqlite3.Row
    db.create_tables(c)
    db.upsert(
        c,
        "receita_orcamentaria",
        [
            {
                "ano": 2024,
                "empresa": "7",
                "codigo": "01",
                "descricao": "IPTU",
                "previsto": "100000",
                "arrecadado": "80000",
            }
        ],
        ["ano", "empresa", "codigo"],
    )
    db.upsert(
        c,
        "receita_uniao",
        [
            {
                "ano": 2024,
                "empresa": "7",
                "codigo": "FPM",
                "descricao": "FPM",
                "previsto": "500000",
                "arrecadado": "500000",
            }
        ],
        ["ano", "empresa", "codigo"],
    )
    db.upsert(
        c,
        "receita_estado",
        [
            {
                "ano": 2024,
                "empresa": "7",
                "codigo": "ICMS",
                "descricao": "ICMS",
                "previsto": "200000",
                "arrecadado": "200000",
            }
        ],
        ["ano", "empresa", "codigo"],
    )
    yield c
    c.close()


def test_revenue_breakdown(conn):
    df = run(conn, [2024])
    row = df[df["ano"] == 2024].iloc[0]
    assert row["receita_propria"] == pytest.approx(80000, rel=0.01)
    assert row["transferencias_uniao"] == pytest.approx(500000, rel=0.01)
    assert row["pct_propria"] == pytest.approx(10.26, rel=0.1)
    assert row["alerta_dependencia"] is False


def test_flags_high_dependency(conn):  # noqa: ARG001
    c = sqlite3.connect(":memory:")
    c.row_factory = sqlite3.Row
    db.create_tables(c)
    db.upsert(
        c,
        "receita_orcamentaria",
        [{"ano": 2024, "empresa": "7", "codigo": "01", "descricao": "X", "previsto": "10000", "arrecadado": "5000"}],
        ["ano", "empresa", "codigo"],
    )
    db.upsert(
        c,
        "receita_uniao",
        [
            {
                "ano": 2024,
                "empresa": "7",
                "codigo": "FPM",
                "descricao": "FPM",
                "previsto": "900000",
                "arrecadado": "900000",
            }
        ],
        ["ano", "empresa", "codigo"],
    )
    df = run(c, [2024])
    assert df[df["ano"] == 2024].iloc[0]["alerta_dependencia"] is True
    c.close()
