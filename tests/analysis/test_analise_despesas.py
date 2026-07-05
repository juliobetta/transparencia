import pytest

import db
from analysis.analise_despesas import (
    get_despesas_por_unidade,
    get_impacto_gastos_locais,
    get_metricas_gerais_despesas,
    get_principais_beneficiarios_diarias,
    get_principais_fornecedores_detalhados,
    get_resumo_diarias,
    get_transacoes_pesquisaveis,
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
        "despesas_gerais",
        [
            {
                "ano": 2026,
                "empresa": "7",
                "numero": "10",
                "nomefor": "Empresa A",
                "elemento": "30",
            },
            {
                "ano": 2026,
                "empresa": "7",
                "numero": "11",
                "nomefor": "Empresa B",
                "elemento": "39",
            },
        ],
        ["ano", "empresa", "numero"],
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
    return conn


def test_get_metricas_gerais_despesas(conn):
    res = get_metricas_gerais_despesas(conn, 2026)
    assert res["empenhado"] == 15000.0
    assert res["liquidado"] == 13000.0
    assert res["pago"] == 11000.0
    assert res["taxa_liquidacao"] == pytest.approx(86.66, rel=0.01)


def test_get_despesas_por_unidade(conn):
    df = get_despesas_por_unidade(conn, 2026)
    assert len(df) == 2
    assert df.iloc[0]["descricao"] == "Saude"
    assert df.iloc[0]["pago"] == 7000.0


def test_get_impacto_gastos_locais(conn):
    res = get_impacto_gastos_locais(conn, 2026)
    assert res["local_pago"] == 3000.0
    assert res["externo_pago"] == 2000.0
    assert res["pct_local"] == 60.0


def test_get_resumo_diarias(conn):
    res = get_resumo_diarias(conn, 2026)
    assert res["total_valor"] == 1900.0
    assert res["total_viajantes"] == 2


def test_get_principais_fornecedores_detalhados(conn):
    df = get_principais_fornecedores_detalhados(conn, 2026)
    assert len(df) == 2
    assert df.iloc[0]["fornecedor"] == "Empresa A"
    assert df.iloc[0]["pago"] == 3000.0


def test_get_principais_beneficiarios_diarias(conn):
    df = get_principais_beneficiarios_diarias(conn, 2026)
    assert len(df) == 2
    assert df.iloc[0]["favorecido"] == "Servidor Y"
    assert df.iloc[0]["valor"] == 1000.0
    assert df.iloc[0]["viagens"] == 1


def test_get_transacoes_pesquisaveis(conn):
    df = get_transacoes_pesquisaveis(conn, 2026, "Empresa")
    assert len(df) >= 1
