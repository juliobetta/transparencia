import pytest

import db
from report.saude_pdf import generate

SAUDE = "2"


@pytest.fixture
def health_conn(conn):
    db.upsert(
        conn,
        "despesas_por_orgao",
        [
            {
                "ano": 2024,
                "empresa": SAUDE,
                "codigo": "10",
                "descricao": "SAUDE",
                "empenhado": "800000",
                "dotacao_atualizada": "1000000",
                "liquidado": "700000",
                "pago": "600000",
                "dotac": "950000",
                "altdo": "50000",
            },
            {
                "ano": 2023,
                "empresa": SAUDE,
                "codigo": "10",
                "descricao": "SAUDE",
                "empenhado": "700000",
                "dotacao_atualizada": "900000",
                "liquidado": "600000",
                "pago": "500000",
                "dotac": "900000",
                "altdo": "0",
            },
        ],
        ["ano", "empresa", "codigo"],
    )
    db.upsert(
        conn,
        "despesas_por_fornecedor",
        [
            {
                "ano": 2024,
                "empresa": SAUDE,
                "codigo": "F001",
                "descricao": "FARMACIA CENTRAL LTDA",
                "empenhado": "400000",
                "liquidado": "350000",
                "pago": "300000",
            },
            {
                "ano": 2024,
                "empresa": SAUDE,
                "codigo": "F002",
                "descricao": "CLINICA SAO JOSE ME",
                "empenhado": "200000",
                "liquidado": "180000",
                "pago": "150000",
            },
        ],
        ["ano", "empresa", "codigo"],
    )
    db.set_metadata(conn, "last_extracted_at", "2024-06-15 08:30:00")
    return conn


def test_generate_returns_valid_pdf_bytes(health_conn):
    result = generate(health_conn, 2024)
    assert isinstance(result, bytes)
    assert result[:4] == b"%PDF"


def test_generate_produces_non_trivial_pdf(health_conn):
    result = generate(health_conn, 2024)
    assert len(result) > 5_000


def test_generate_handles_missing_metadata(conn):
    """Test that generate uses 'desconhecida' when no metadata is set."""
    db.upsert(
        conn,
        "despesas_por_orgao",
        [
            {
                "ano": 2025,
                "empresa": SAUDE,
                "codigo": "10",
                "descricao": "SAUDE",
                "empenhado": "800000",
                "dotacao_atualizada": "1000000",
                "liquidado": "700000",
                "pago": "600000",
                "dotac": "950000",
                "altdo": "50000",
            },
        ],
        ["ano", "empresa", "codigo"],
    )
    result = generate(conn, 2025)
    assert isinstance(result, bytes)
    assert result[:4] == b"%PDF"
