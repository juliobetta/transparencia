import pytest

import db
from analysis.expenses_analysis import (
    get_diarias_summary,
    get_expenses_by_unit,
    get_general_expense_metrics,
    get_local_spending_impact,
    get_searchable_transactions,
    get_top_diarias_beneficiaries,
    get_top_suppliers_detailed,
)


@pytest.fixture
def conn(conn):
    db.upsert(
        conn,
        "despesas_por_unidade",
        [
            {
                "ano": 2026,
                "empresa": "7",
                "codigo": "1",
                "descricao": "Saude",
                "empenhado": "10000",
                "liquidado": "8000",
                "pago": "7000",
                "dotacao_atualizada": "12000",
            },
            {
                "ano": 2026,
                "empresa": "7",
                "codigo": "2",
                "descricao": "Educacao",
                "empenhado": "5000",
                "liquidado": "5000",
                "pago": "4000",
                "dotacao_atualizada": "6000",
            },
        ],
        ["ano", "empresa", "codigo"],
    )
    db.upsert(
        conn,
        "despesas_por_fornecedor",
        [
            {
                "ano": 2026,
                "empresa": "7",
                "codigo": "301",
                "descricao": "Empresa A",
                "insmf": "123",
                "cepci": "PORCIUNCULA",
                "empenhado": "5000",
                "liquidado": "4000",
                "pago": "3000",
            },
            {
                "ano": 2026,
                "empresa": "7",
                "codigo": "302",
                "descricao": "Empresa B",
                "insmf": "456",
                "cepci": "RIO DE JANEIRO",
                "empenhado": "3000",
                "liquidado": "3000",
                "pago": "2000",
            },
        ],
        ["ano", "empresa", "codigo"],
    )
    db.upsert(
        conn,
        "diarias",
        [
            {
                "ano": 2026,
                "empresa": "7",
                "numero": "1",
                "favorecido": "Servidor X",
                "cargo": "Motorista",
                "valor": "500",
            },
            {
                "ano": 2026,
                "empresa": "7",
                "numero": "2",
                "favorecido": "Servidor X",
                "cargo": "Motorista",
                "valor": "400",
            },
            {
                "ano": 2026,
                "empresa": "7",
                "numero": "3",
                "favorecido": "Servidor Y",
                "cargo": "Prefeito",
                "valor": "1000",
            },
        ],
        ["ano", "empresa", "numero"],
    )
    db.upsert(
        conn,
        "despesas_gerais",
        [
            {
                "ano": 2026,
                "empresa": "7",
                "numero": "10",
                "datae": "01/01/2026",
                "nomefor": "Fornecedor X",
                "pago": "5000",
                "nomeempresa": "Saude",
                "produ": "compra de ambulancia",
            },
            {
                "ano": 2026,
                "empresa": "7",
                "numero": "11",
                "datae": "02/01/2026",
                "nomefor": "Fornecedor Y",
                "pago": "12000",
                "nomeempresa": "Educacao",
                "produ": "merenda escolar",
            },
        ],
        ["ano", "empresa", "numero"],
    )
    return conn


def test_get_general_expense_metrics(conn):
    res = get_general_expense_metrics(conn, 2026)
    assert res["empenhado"] == 15000.0
    assert res["liquidado"] == 13000.0
    assert res["pago"] == 11000.0
    assert res["taxa_liquidacao"] == pytest.approx(86.66, rel=0.01)


def test_get_expenses_by_unit(conn):
    df = get_expenses_by_unit(conn, 2026)
    assert len(df) == 2
    assert df.iloc[0]["descricao"] == "Saude"
    assert df.iloc[0]["pago"] == 7000.0


def test_get_local_spending_impact(conn):
    res = get_local_spending_impact(conn, 2026)
    assert res["local_pago"] == 3000.0
    assert res["externo_pago"] == 2000.0
    assert res["pct_local"] == 60.0


def test_get_diarias_summary(conn):
    res = get_diarias_summary(conn, 2026)
    assert res["total_valor"] == 1900.0
    assert res["total_viajantes"] == 2


def test_get_top_suppliers_detailed(conn):
    df = get_top_suppliers_detailed(conn, 2026)
    assert len(df) == 2
    assert df.iloc[0]["fornecedor"] == "Empresa A"
    assert df.iloc[0]["pago"] == 3000.0


def test_get_top_diarias_beneficiaries(conn):
    df = get_top_diarias_beneficiaries(conn, 2026)
    assert len(df) == 2
    assert df.iloc[0]["favorecido"] == "Servidor Y"
    assert df.iloc[0]["valor"] == 1000.0
    assert df.iloc[0]["viagens"] == 1


def test_get_searchable_transactions(conn):
    df = get_searchable_transactions(conn, 2026, "merenda")
    assert len(df) == 1
    assert df.iloc[0]["fornecedor"] == "Fornecedor Y"
