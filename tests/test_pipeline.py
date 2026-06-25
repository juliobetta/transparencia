import sqlite3
from unittest.mock import patch

import pytest

import db
import pipeline


@pytest.fixture
def mem_conn(monkeypatch):
    conn = sqlite3.connect(":memory:")
    conn.row_factory = sqlite3.Row
    db.create_tables(conn)
    monkeypatch.setattr(pipeline, "get_connection", lambda: conn)
    return conn


def test_run_upserts_data_for_all_entities(mem_conn):
    fetch_results = {
        "DespesasPorOrgao": [
            {
                "EMPRESA": "7",
                "CODIGO": "01",
                "DESCRICAO": "SAUDE",
                "EMPENHADO": "100",
                "LIQUIDADO": "90",
                "PAGO": "80",
                "DOTAC": "200",
                "ALTDO": "0",
                "DOTACAO_ATUALIZADA": "200",
            }
        ],
    }

    def fake_fetch(url):
        for listagem, rows in fetch_results.items():
            if listagem in url:
                return rows
        return []

    with patch("extractors.base.fetch", side_effect=fake_fetch):
        pipeline.run(years=[2025])

    cur = mem_conn.execute("SELECT COUNT(*) FROM despesas_por_orgao WHERE ano=2025")
    assert cur.fetchone()[0] >= 1


def test_run_logs_and_skips_on_fetch_error(mem_conn, caplog):  # noqa: ARG001
    import logging

    def bad_fetch(url):
        if "DespesasPorOrgao" in url:
            raise RuntimeError("timeout")
        return []

    with patch("extractors.base.fetch", side_effect=bad_fetch):
        with caplog.at_level(logging.WARNING):
            pipeline.run(years=[2025])

    assert any("timeout" in r.message for r in caplog.records)
