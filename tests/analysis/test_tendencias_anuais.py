import pytest

import db
from analysis.tendencias_anuais import run


@pytest.fixture
def conn(conn):
    for year, pago in [(2023, "800000"), (2024, "1000000")]:
        db.upsert(
            conn,
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
                },
            ],
            ["ano", "empresa", "codigo"],
        )
    return conn


def test_returns_expected_columns(conn):
    df = run(conn, [2023, 2024])
    assert {"ano", "total_gasto", "total_gasto_pct_change"}.issubset(df.columns)


def test_pct_change_computed(conn):
    df = run(conn, [2023, 2024])
    row_2024 = df[df["ano"] == 2024].iloc[0]
    assert row_2024["total_gasto_pct_change"] == pytest.approx(25.0, rel=0.01)


def test_revenue_root_only_avoids_double_counting(conn):
    """YoY total_receita must use root-level codes only."""
    db.upsert(
        conn,
        "receita_orcamentaria",
        [
            {
                "ano": 2024,
                "empresa": "7",
                "codigo": "1000.00.0.0.00.00",
                "descricao": "Receitas Correntes",
                "previsto": "100000",
                "arrecadado": "90000",
                "previsao_atualizada": "100000",
                "arrecadado_total": "90000",
            },
            {
                "ano": 2024,
                "empresa": "7",
                "codigo": "1100.00.0.0.00.00",
                "descricao": "Receita Tributária",
                "previsto": "40000",
                "arrecadado": "36000",
                "previsao_atualizada": "40000",
                "arrecadado_total": "36000",
            },
        ],
        ["ano", "empresa", "codigo"],
    )
    df = run(conn, [2024])
    row = df[df["ano"] == 2024].iloc[0]
    # Root (90000) only, not root + child (90000 + 36000 = 126000)
    assert row["total_receita"] == pytest.approx(90000, rel=0.01)
