import sqlite3

import pandas as pd
import pytest

from analysis.caprem_story import run


@pytest.fixture
def conn():
    c = sqlite3.connect(":memory:")
    c.row_factory = sqlite3.Row
    c.execute(
        "CREATE TABLE despesas_por_fornecedor (ano INTEGER, empresa TEXT, codigo TEXT, descricao TEXT, empenhado TEXT, liquidado TEXT, pago TEXT, insmf TEXT, cepci TEXT)"
    )
    c.execute(
        "INSERT INTO despesas_por_fornecedor VALUES (2023, '7', '1061', 'CAPREM-CAIXA DE PREVIDENCIA MUNICIPAL', '1556335,93', '1556335,93', '1556335,93', '01.180.031/0001-34', 'PORCIUNCULA')"
    )
    return c


def test_run_returns_expected_structure(conn):
    result = run(conn, 2023)
    assert result["total_transfers"] == 1556335.93
    assert result["count_operations"] == 1
    assert isinstance(result["despesas"], pd.DataFrame)
    assert result["transfers_by_type"] == []
    assert result["budget"] == {"dotacao": 0, "empenhado": 0, "taxa_execucao": 0}
