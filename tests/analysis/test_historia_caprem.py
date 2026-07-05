import pandas as pd
import pytest

import db
from analysis.historia_caprem import run


@pytest.fixture
def conn(conn):
    db.upsert(
        conn,
        "despesas_por_fornecedor",
        [
            {
                "ano": 2023,
                "empresa": "7",
                "codigo": "1061",
                "descricao": "CAPREM-CAIXA DE PREVIDENCIA MUNICIPAL",
                "empenhado": "1556335,93",
                "liquidado": "1556335,93",
                "pago": "1556335,93",
                "insmf": "01.180.031/0001-34",
                "cepci": "PORCIUNCULA",
            },
        ],
        ["ano", "empresa", "codigo"],
    )
    return conn


def test_run_returns_expected_structure(conn):
    result = run(conn, 2023)
    assert result["total_transferencias"] == pytest.approx(1556335.93, rel=0.01)
    assert result["count_operacoes"] == 1
    assert isinstance(result["despesas"], pd.DataFrame)
    assert result["transferencias_por_tipo"] == []
    assert result["orcamento"] == {"dotacao": 0, "empenhado": 0, "taxa_execucao": 0}
