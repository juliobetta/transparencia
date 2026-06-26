import pytest

import db
from analysis.revenue_sources import run


@pytest.fixture
def conn(conn):
    db.upsert(
        conn,
        "receita_orcamentaria",
        [
            {
                "ano": 2024,
                "empresa": "7",
                "codigo": "01",
                "descricao": "IPTU",
                "previsto": "100000",
                "arrecadado": "80000",
                "previsao_atualizada": "100000",
                "arrecadado_total": "80000",
            },
        ],
        ["ano", "empresa", "codigo"],
    )
    db.upsert(
        conn,
        "receita_uniao",
        [
            {
                "ano": 2024,
                "empresa": "7",
                "codigo": "FPM",
                "descricao": "FPM",
                "previsto": "500000",
                "arrecadado": "500000",
                "previsao_atualizada": "500000",
                "arrecadado_total": "500000",
            },
        ],
        ["ano", "empresa", "codigo"],
    )
    db.upsert(
        conn,
        "receita_estado",
        [
            {
                "ano": 2024,
                "empresa": "7",
                "codigo": "ICMS",
                "descricao": "ICMS",
                "previsto": "200000",
                "arrecadado": "200000",
                "previsao_atualizada": "200000",
                "arrecadado_total": "200000",
            },
        ],
        ["ano", "empresa", "codigo"],
    )
    return conn


def test_revenue_breakdown(conn):
    df = run(conn, [2024])
    row = df[df["ano"] == 2024].iloc[0]
    assert row["receita_propria"] == pytest.approx(80000, rel=0.01)
    assert row["transferencias_uniao"] == pytest.approx(500000, rel=0.01)
    assert row["pct_propria"] == pytest.approx(10.26, rel=0.1)
    assert row["alerta_dependencia"] is False
    assert row["receita_propria_arrecadado"] == 80000.0


def test_flags_high_dependency(conn):
    # Insert high-dependency data for a different year to avoid conflict
    db.upsert(
        conn,
        "receita_orcamentaria",
        [
            {
                "ano": 2020,
                "empresa": "7",
                "codigo": "01",
                "descricao": "X",
                "previsto": "10000",
                "arrecadado": "5000",
                "previsao_atualizada": "10000",
                "arrecadado_total": "5000",
            },
        ],
        ["ano", "empresa", "codigo"],
    )
    db.upsert(
        conn,
        "receita_uniao",
        [
            {
                "ano": 2020,
                "empresa": "7",
                "codigo": "FPM",
                "descricao": "FPM",
                "previsto": "900000",
                "arrecadado": "900000",
                "previsao_atualizada": "900000",
                "arrecadado_total": "900000",
            },
        ],
        ["ano", "empresa", "codigo"],
    )
    df = run(conn, [2020])
    assert df[df["ano"] == 2020].iloc[0]["alerta_dependencia"] is True
