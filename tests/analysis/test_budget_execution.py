import pandas as pd
import pytest

import db
from analysis.budget_execution import run


@pytest.fixture
def conn(conn):
    db.upsert(
        conn,
        "despesas_por_orgao",
        [
            {
                "ano": 2025,
                "empresa": "7",
                "codigo": "01",
                "descricao": "SAUDE",
                "empenhado": "100000",
                "liquidado": "90000",
                "pago": "80000",
                "dotac": "500000",
                "altdo": "0",
                "dotacao_atualizada": "500000",
            },
            {
                "ano": 2025,
                "empresa": "7",
                "codigo": "02",
                "descricao": "EDUCACAO",
                "empenhado": "600000",
                "liquidado": "600000",
                "pago": "600000",
                "dotac": "500000",
                "altdo": "0",
                "dotacao_atualizada": "500000",
            },
            {
                "ano": 2025,
                "empresa": "7",
                "codigo": "03",
                "descricao": "CULTURA",
                "empenhado": "250000",
                "liquidado": "200000",
                "pago": "200000",
                "dotac": "500000",
                "altdo": "0",
                "dotacao_atualizada": "500000",
            },
        ],
        ["ano", "empresa", "codigo"],
    )
    return conn


def test_returns_dataframe_with_expected_columns(conn):
    df = run(conn, 2025)
    assert isinstance(df, pd.DataFrame)
    assert {"codigo", "descricao", "taxa_execucao", "alerta"}.issubset(df.columns)


def test_flags_low_execution(conn):
    df = run(conn, 2025)
    saude = df[df["codigo"] == "01"].iloc[0]
    assert saude["taxa_execucao"] == pytest.approx(0.2, rel=0.01)
    assert saude["alerta"] == "baixa"


def test_flags_overspend(conn):
    df = run(conn, 2025)
    edu = df[df["codigo"] == "02"].iloc[0]
    assert edu["taxa_execucao"] == pytest.approx(1.2, rel=0.01)
    assert edu["alerta"] == "excesso"


def test_flags_normal(conn):
    df = run(conn, 2025)
    cultura = df[df["codigo"] == "03"].iloc[0]
    assert cultura["alerta"] == "normal"
