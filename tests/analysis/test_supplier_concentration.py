import sqlite3

import pytest

import db
from analysis.supplier_concentration import run


@pytest.fixture
def conn():
    c = sqlite3.connect(":memory:")
    c.row_factory = sqlite3.Row
    db.create_tables(c)
    rows = [
        {
            "ano": 2025,
            "empresa": "7",
            "codigo": "01",
            "descricao": "ALFA LTDA",
            "empenhado": "600000",
            "liquidado": "0",
            "pago": "0",
        },
        {
            "ano": 2025,
            "empresa": "7",
            "codigo": "02",
            "descricao": "BETA ME",
            "empenhado": "200000",
            "liquidado": "0",
            "pago": "0",
        },
        {
            "ano": 2025,
            "empresa": "7",
            "codigo": "03",
            "descricao": "GAMA SA",
            "empenhado": "200000",
            "liquidado": "0",
            "pago": "0",
        },
    ]
    db.upsert(c, "despesas_por_fornecedor", rows, ["ano", "empresa", "codigo"])
    yield c
    c.close()


def test_top10_has_correct_columns(conn):
    result = run(conn, 2025)
    assert {"codigo", "descricao", "empenhado", "percentual"}.issubset(result["top10"].columns)


def test_top10_sorted_descending(conn):
    result = run(conn, 2025)
    vals = result["top10"]["empenhado"].tolist()
    assert vals == sorted(vals, reverse=True)


def test_hhi_computed(conn):
    result = run(conn, 2025)
    # shares: 0.6, 0.2, 0.2 → HHI = 0.6²+0.2²+0.2² * 10000 = 4400
    assert result["hhi"] == pytest.approx(4400, rel=0.01)


def test_dominant_supplier_detected(conn):
    result = run(conn, 2025)
    assert result["dominante"] == "ALFA LTDA"


def test_no_dominant_when_balanced():
    c = sqlite3.connect(":memory:")
    c.row_factory = sqlite3.Row
    db.create_tables(c)
    rows = [
        {
            "ano": 2025,
            "empresa": "7",
            "codigo": str(i),
            "descricao": f"F{i}",
            "empenhado": "100000",
            "liquidado": "0",
            "pago": "0",
        }
        for i in range(5)
    ]
    db.upsert(c, "despesas_por_fornecedor", rows, ["ano", "empresa", "codigo"])
    result = run(c, 2025)
    assert result["dominante"] is None
    c.close()
