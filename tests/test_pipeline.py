import logging
from unittest.mock import patch

import pytest
from sqlalchemy import text

import pipeline


@pytest.fixture
def mock_engine(monkeypatch, engine):
    monkeypatch.setattr(pipeline, "get_engine", lambda: engine)
    yield engine
    with engine.connect() as conn:
        for table_name in ["despesas_por_orgao", "empresas"]:
            conn.execute(text(f"TRUNCATE TABLE {table_name} CASCADE"))
        conn.commit()


def test_run_upserts_data_for_all_entities(mock_engine):
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

    with mock_engine.connect() as conn:
        count = conn.execute(text("SELECT COUNT(*) FROM despesas_por_orgao WHERE ano=2025")).fetchone()[0]
    assert count >= 1


def test_run_logs_and_skips_on_fetch_error(mock_engine, caplog):  # noqa: ARG001
    def bad_fetch(url):
        if "DespesasPorOrgao" in url:
            raise RuntimeError("timeout")
        return []

    with patch("extractors.base.fetch", side_effect=bad_fetch):
        with caplog.at_level(logging.WARNING):
            pipeline.run(years=[2025])

    assert any("timeout" in r.message for r in caplog.records)
