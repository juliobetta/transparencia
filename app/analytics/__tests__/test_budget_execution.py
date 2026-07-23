import pandas as pd
import pytest

import db
from app.analytics.execucao_orcamentaria import run, summarize, summarize_by_year


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


def test_summarize(conn):
    df = run(conn, 2025)
    summary = summarize(df)
    assert summary["total_dotacao"] == 1500000.0
    assert summary["total_empenhado"] == 950000.0
    assert summary["total_liquidado"] == 890000.0
    assert summary["total_pago"] == 880000.0
    assert summary["saldo_orcamentario"] == 550000.0


def test_summarize_by_year(conn):
    # O fixture insere dados de 2025:
    # SAUDE: dotacao=500000, empenhado=100000, liquidado=90000, pago=80000
    # EDUCACAO: dotacao=500000, empenhado=600000, liquidado=600000, pago=600000
    # CULTURA: dotacao=500000, empenhado=250000, liquidado=200000, pago=200000
    result = summarize_by_year(conn, [2025])
    assert 2025 in result
    assert result[2025]["total_dotacao"] == 1500000.0
    assert result[2025]["total_empenhado"] == 950000.0
    assert result[2025]["total_pago"] == 880000.0
