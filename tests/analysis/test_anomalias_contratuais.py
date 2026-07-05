import pytest

import db
from analysis.anomalias_contratuais import run


@pytest.fixture
def conn(conn):
    contratos = [
        {
            "ano": 2025,
            "empresa": "7",
            "numero": str(i),
            "fornecedor": "ALFA LTDA",
            "objeto": "SERVICO",
            "valcon": "55000",
            "data_inicio": "2025-01-01",
            "data_fim": "2025-03-31",
            "licitacao_numero": "",
        }
        for i in range(1, 5)
    ]
    db.upsert(conn, "contratos", contratos, ["ano", "empresa", "numero"])
    return conn


def test_fracionamento_detecta_padrao(conn):
    result = run(conn, 2025)
    assert "ALFA LTDA" in result["fracionamento"]["fornecedor"].values


def test_resultado_tem_todas_as_chaves(conn):
    result = run(conn, 2025)
    assert {"fracionamento", "fornecedor_recorrente", "janela_curta"} == set(result.keys())
