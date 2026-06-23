import sqlite3

import pytest

import db
from analysis.bidding_gaps import run

SAUDE_EMPRESA = "2"


@pytest.fixture
def conn():
    c = sqlite3.connect(":memory:")
    c.row_factory = sqlite3.Row
    db.create_tables(c)
    contratos = [
        {
            "ano": 2025,
            "empresa": SAUDE_EMPRESA,
            "numero": "001",
            "fornecedor": "ALFA LTDA",
            "objeto": "REMÉDIOS",
            "valor": "200000",
            "data_inicio": "2025-01-01",
            "data_fim": "2025-12-31",
            "licitacao_numero": "",
        },
        {
            "ano": 2025,
            "empresa": SAUDE_EMPRESA,
            "numero": "002",
            "fornecedor": "BETA ME",
            "objeto": "MATERIAL",
            "valor": "10000",
            "data_inicio": "2025-01-01",
            "data_fim": "2025-12-31",
            "licitacao_numero": "",
        },
        {
            "ano": 2025,
            "empresa": "7",
            "numero": "003",
            "fornecedor": "GAMA SA",
            "objeto": "OBRA",
            "valor": "500000",
            "data_inicio": "2025-01-01",
            "data_fim": "2025-12-31",
            "licitacao_numero": "LC-001",
        },
    ]
    db.upsert(c, "contratos", contratos, ["ano", "empresa", "numero"])
    yield c
    c.close()


def test_excludes_contracts_with_licitacao(conn):
    df = run(conn, 2025)
    assert "003" not in df["numero"].values


def test_flags_above_threshold(conn):
    df = run(conn, 2025)
    row = df[df["numero"] == "001"].iloc[0]
    assert row["acima_limite"]


def test_below_threshold_not_flagged(conn):
    df = run(conn, 2025)
    row = df[df["numero"] == "002"].iloc[0]
    assert not row["acima_limite"]


def test_flags_saude_empresa(conn):
    df = run(conn, 2025)
    assert df[df["numero"] == "001"].iloc[0]["orgao_saude"]
