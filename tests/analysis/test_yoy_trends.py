import sqlite3

import pytest

import db
from analysis.yoy_trends import run


@pytest.fixture
def conn():
    c = sqlite3.connect(":memory:")
    c.row_factory = sqlite3.Row
    db.create_tables(c)
    for year, pago in [(2023, "800000"), (2024, "1000000")]:
        db.upsert(
            c,
            "despesas_por_orgao",
            [
                {
                    "ano": year,
                    "empresa": "7",
                    "codigo": "01",
                    "descricao": "X",
                    "empenhado": pago,
                    "liquidado": pago,
                    "pago": pago,
                    "dotac": pago,
                    "altdo": "0",
                    "dotacao_atualizada": pago,
                }
            ],
            ["ano", "empresa", "codigo"],
        )
    yield c
    c.close()


def test_returns_expected_columns(conn):
    df = run(conn, [2023, 2024])
    assert {"ano", "total_gasto", "total_gasto_pct_change"}.issubset(df.columns)


def test_pct_change_computed(conn):
    df = run(conn, [2023, 2024])
    row_2024 = df[df["ano"] == 2024].iloc[0]
    assert row_2024["total_gasto_pct_change"] == pytest.approx(25.0, rel=0.01)
