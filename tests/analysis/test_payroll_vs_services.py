import pytest

import db
from analysis.payroll_vs_services import run


@pytest.fixture
def conn(conn):
    db.upsert(
        conn,
        "despesas_por_orgao",
        [
            {
                "ano": 2024,
                "empresa": "7",
                "codigo": "01",
                "descricao": "SAUDE",
                "empenhado": "1000000",
                "liquidado": "900000",
                "pago": "800000",
                "dotac": "1000000",
                "altdo": "0",
                "dotacao_atualizada": "1000000",
            },
        ],
        ["ano", "empresa", "codigo"],
    )
    db.upsert(
        conn,
        "pessoal",
        [
            {
                "ano": 2024,
                "empresa": "7",
                "mes": "01",
                "matricula": "001",
                "nome": "JOAO",
                "cargo": "AGENTE",
                "proventos": "300000",
            },
            {
                "ano": 2024,
                "empresa": "7",
                "mes": "02",
                "matricula": "001",
                "nome": "JOAO",
                "cargo": "AGENTE",
                "proventos": "300000",
            },
        ],
        ["ano", "empresa", "mes", "matricula"],
    )
    return conn


def test_returns_dataframe_with_percentual(conn):
    df = run(conn, [2024])
    assert "percentual_folha" in df.columns
    row = df[df["ano"] == 2024].iloc[0]
    assert row["total_folha"] == pytest.approx(600000, rel=0.01)
    assert row["total_gasto"] == pytest.approx(800000, rel=0.01)
    assert row["percentual_folha"] == pytest.approx(75.0, rel=0.01)
