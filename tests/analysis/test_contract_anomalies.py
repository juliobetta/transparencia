import sqlite3

import pytest

import db
from analysis.contract_anomalies import run


@pytest.fixture
def conn():
    c = sqlite3.connect(":memory:")
    c.row_factory = sqlite3.Row
    db.create_tables(c)
    # splitting pattern: 4 contracts just below 57k from same supplier
    contratos = [
        {
            "ano": 2025,
            "empresa": "7",
            "numero": str(i),
            "fornecedor": "ALFA LTDA",
            "objeto": "SERVICO",
            "valor": "55000",
            "data_inicio": "2025-01-01",
            "data_fim": "2025-03-31",
            "licitacao_numero": "",
        }
        for i in range(1, 5)
    ]
    db.upsert(c, "contratos", contratos, ["ano", "empresa", "numero"])
    yield c
    c.close()


def test_splitting_detects_pattern(conn):
    result = run(conn, 2025)
    assert "ALFA LTDA" in result["splitting"]["fornecedor"].values


def test_result_has_all_keys(conn):
    result = run(conn, 2025)
    assert {"splitting", "repeated_supplier", "short_window"} == set(result.keys())
