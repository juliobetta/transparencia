import sqlite3

import pytest

from analysis.caprem_story import run


@pytest.fixture
def conn():
    c = sqlite3.connect(":memory:")
    c.row_factory = sqlite3.Row
    return c


def test_run_returns_expected_structure(conn):
    result = run(conn, 2023)
    assert result["total_transfers"] == 0
    assert result["transfers_by_type"] == []
    assert result["budget"] == {"dotacao": 0, "empenhado": 0, "taxa_execucao": 0}
