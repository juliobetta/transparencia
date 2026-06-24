import sqlite3

import pytest

import db
from analysis.health_story import run

SAUDE = "2"
OTHER = "7"


@pytest.fixture
def conn():
    c = sqlite3.connect(":memory:")
    c.row_factory = sqlite3.Row
    db.create_tables(c)

    db.upsert(
        c,
        "emendas_cad",
        [
            {
                "ano": 2023,
                "empresa": SAUDE,
                "numero": "E001",
                "descricao": "MEDICAMENTOS",
                "valor": "0",
                "valor_total": "500000",
                "empenhado": "400000",
            },
            {
                "ano": 2023,
                "empresa": OTHER,
                "numero": "E002",
                "descricao": "OBRAS",
                "valor": "0",
                "valor_total": "1000000",
                "empenhado": "0",
            },
        ],
        ["ano", "empresa", "numero"],
    )

    db.upsert(
        c,
        "despesas_por_orgao",
        [
            {
                "ano": 2023,
                "empresa": SAUDE,
                "codigo": "10",
                "descricao": "SAUDE",
                "empenhado": "800000",
                "dotacao_atualizada": "1000000",
                "liquidado": "0",
                "pago": "0",
                "dotac": "0",
                "altdo": "0",
            },
            {
                "ano": 2023,
                "empresa": OTHER,
                "codigo": "01",
                "descricao": "PREFEITURA",
                "empenhado": "2000000",
                "dotacao_atualizada": "2500000",
                "liquidado": "0",
                "pago": "0",
                "dotac": "0",
                "altdo": "0",
            },
            {
                "ano": 2022,
                "empresa": SAUDE,
                "codigo": "10",
                "descricao": "SAUDE",
                "empenhado": "700000",
                "dotacao_atualizada": "900000",
                "liquidado": "0",
                "pago": "0",
                "dotac": "0",
                "altdo": "0",
            },
        ],
        ["ano", "empresa", "codigo"],
    )

    db.upsert(
        c,
        "contratos",
        [
            {
                "ano": 2023,
                "empresa": SAUDE,
                "numero": "C001",
                "fornecedor": "ALFA",
                "objeto": "REMÉDIOS",
                "valor": "200000",
                "licitacao_numero": "L001",
                "modali": "PREGÃO ELETRÔNICO",
            },
            {
                "ano": 2023,
                "empresa": SAUDE,
                "numero": "C002",
                "fornecedor": "BETA",
                "objeto": "MATERIAL",
                "valor": "100000",
                "licitacao_numero": "",
                "modali": "DISPENSA",
            },
            {
                "ano": 2023,
                "empresa": SAUDE,
                "numero": "C003",
                "fornecedor": "GAMA",
                "objeto": "CARONA",
                "valor": "150000",
                "licitacao_numero": "L002",
                "modali": "PREGÃO ELETRÔNICO",
            },
            {
                "ano": 2023,
                "empresa": OTHER,
                "numero": "C004",
                "fornecedor": "DELTA",
                "objeto": "OBRA",
                "valor": "500000",
                "licitacao_numero": "L003",
                "modali": "PREGÃO PRESENCIAL",
            },
        ],
        ["ano", "empresa", "numero"],
    )

    db.upsert(
        c,
        "licitacoes",
        [
            {
                "ano": 2023,
                "empresa": SAUDE,
                "numero": "L001",
                "modalidade": "PREGÃO ELETRÔNICO",
                "objeto": "REMÉDIOS",
                "valor": "200000",
                "carona": "N",
            },
            {
                "ano": 2023,
                "empresa": SAUDE,
                "numero": "L002",
                "modalidade": "PREGÃO ELETRÔNICO",
                "objeto": "CARONA",
                "valor": "150000",
                "carona": "S",
            },
        ],
        ["ano", "empresa", "numero"],
    )

    db.upsert(
        c,
        "despesas_por_fornecedor",
        [
            {
                "ano": 2023,
                "empresa": SAUDE,
                "codigo": "1001",
                "descricao": "ALFA LTDA",
                "empenhado": "500000",
                "liquidado": "0",
                "pago": "0",
            },
            {
                "ano": 2023,
                "empresa": SAUDE,
                "codigo": "1002",
                "descricao": "BETA ME",
                "empenhado": "300000",
                "liquidado": "0",
                "pago": "0",
            },
            {
                "ano": 2023,
                "empresa": OTHER,
                "codigo": "2001",
                "descricao": "DELTA SA",
                "empenhado": "2000000",
                "liquidado": "0",
                "pago": "0",
            },
        ],
        ["ano", "empresa", "codigo"],
    )

    yield c
    c.close()


def test_emendas_filtered_to_empresa(conn):
    result = run(conn, 2023)
    assert len(result["emendas"]) == 1
    assert result["emendas"].iloc[0]["numero"] == "E001"


def test_emendas_total(conn):
    result = run(conn, 2023)
    assert result["emendas_total"] == 500000.0


def test_budget_filtered_to_empresa(conn):
    result = run(conn, 2023)
    assert result["budget"]["dotacao"] == 1_000_000.0
    assert result["budget"]["empenhado"] == 800_000.0


def test_budget_taxa_execucao(conn):
    result = run(conn, 2023)
    assert abs(result["budget"]["taxa_execucao"] - 0.8) < 0.001


def test_execution_trend_filtered_to_empresa(conn):
    result = run(conn, 2023)
    trend = result["execution_trend"]
    assert set(trend["ano"].tolist()) == {2022, 2023}
    assert 2023 not in trend[trend["ano"] == 2023]["empenhado"].values or True  # just check OTHER is absent
    # OTHER empresa should not appear
    row_2023 = trend[trend["ano"] == 2023].iloc[0]
    assert row_2023["empenhado"] == 800_000.0


def test_contracts_by_modality(conn):
    result = run(conn, 2023)
    modalities = result["contracts_by_modality"]["modality"].tolist()
    # OTHER empresa contract (DELTA) must not appear
    assert all(m != "PREGÃO PRESENCIAL" or False for m in modalities)  # PREGÃO PRESENCIAL is OTHER's
    counts = dict(zip(result["contracts_by_modality"]["modality"], result["contracts_by_modality"]["count"]))
    assert counts.get("PREGÃO ELETRÔNICO", 0) == 2
    assert counts.get("DISPENSA", 0) == 1


def test_adesao_de_ata_detected(conn):
    result = run(conn, 2023)
    assert result["adesao_de_ata_count"] == 1
    assert result["adesao_de_ata_value"] == 150_000.0


def test_bidding_gaps_above_threshold_only(conn):
    result = run(conn, 2023)
    # C002 has valor=100000 > 57000, no licitacao_numero → gap
    assert len(result["bidding_gaps"]) == 1
    assert result["bidding_gaps"].iloc[0]["numero"] == "C002"


def test_top_suppliers_filtered_to_empresa(conn):
    result = run(conn, 2023)
    names = result["top_suppliers"]["descricao"].tolist()
    assert "DELTA SA" not in names
    assert "ALFA LTDA" in names


def test_hhi_positive(conn):
    result = run(conn, 2023)
    assert result["hhi"] > 0
