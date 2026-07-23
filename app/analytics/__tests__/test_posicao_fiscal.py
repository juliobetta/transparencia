import pytest

import db
from app.analytics.posicao_fiscal import run


@pytest.fixture
def conn(conn):
    # Receita: código raiz único para revenue_sources somar corretamente
    db.upsert(
        conn,
        "receita_orcamentaria",
        [
            {
                "ano": 2026,
                "empresa": "7",
                "codigo": "1000.00.0.0.00.00",
                "descricao": "Receitas Correntes",
                "previsto": "200000",
                "arrecadado": "180000",
                "previsao_atualizada": "200000",
                "arrecadado_total": "180000",
            }
        ],
        ["ano", "empresa", "codigo"],
    )
    # Despesas pagas (orçamento corrente)
    db.upsert(
        conn,
        "despesas_por_orgao",
        [
            {
                "ano": 2026,
                "empresa": "7",
                "codigo": "01",
                "descricao": "Saúde",
                "empenhado": "100000",
                "liquidado": "90000",
                "pago": "80000",
                "dotac": "100000",
                "altdo": "0",
                "dotacao_atualizada": "100000",
            }
        ],
        ["ano", "empresa", "codigo"],
    )
    # Restos pagos em 2026 (sobre obrigações antigas)
    db.upsert(
        conn,
        "despesas_restos_pagar",
        [
            {
                "ano": 2026,
                "empresa": "7",
                "numero": "001",
                "descricao": "Resto 2026",
                "pago": "30000",
                "codigo": "01",
                "empenhado": "30000",
                "liquidado": "30000",
            }
        ],
        ["ano", "empresa", "numero"],
    )
    # Restos de exercícios anteriores (dívida plurianual)
    db.upsert(
        conn,
        "despesas_restos_pagar",
        [
            {
                "ano": 2024,
                "empresa": "7",
                "numero": "001",
                "descricao": "Resto 2024",
                "pago": "20000",
                "codigo": "01",
                "empenhado": "50000",
                "liquidado": "20000",
            },
            {
                "ano": 2025,
                "empresa": "7",
                "numero": "001",
                "descricao": "Resto 2025",
                "pago": "15000",
                "codigo": "01",
                "empenhado": "40000",
                "liquidado": "15000",
            },
        ],
        ["ano", "empresa", "numero"],
    )
    return conn


def test_saldo_estimado_calculation(conn):
    result = run(conn, 2026)
    # receitas=180000, despesas=80000, restos_paid=30000
    # total_saidas = 80000 + 30000 = 110000
    # saldo = 180000 - 110000 = 70000
    assert result["total_arrecadado"] == pytest.approx(180000, rel=0.01)
    assert result["despesas_pagas"] == pytest.approx(80000, rel=0.01)
    assert result["restos_pagos_no_ano"] == pytest.approx(30000, rel=0.01)
    assert result["total_saidas"] == pytest.approx(110000, rel=0.01)
    assert result["saldo_estimado"] == pytest.approx(70000, rel=0.01)


def test_restos_pendentes_por_ano(conn):
    result = run(conn, 2026)
    by_ano = {r["ano"]: r for r in result["restos_pendentes"]}
    # 2024: empenhado=50000, pago=20000 → pendente=30000
    assert by_ano[2024]["pendente"] == pytest.approx(30000, rel=0.01)
    # 2025: empenhado=40000, pago=15000 → pendente=25000
    assert by_ano[2025]["pendente"] == pytest.approx(25000, rel=0.01)
    # 2026: empenhado=30000, pago=30000 → pendente=0
    assert by_ano[2026]["pendente"] == pytest.approx(0, abs=1)
    # Total pendente = 30000 + 25000 + 0 = 55000
    assert result["restos_pendentes_total"] == pytest.approx(55000, rel=0.01)


def test_fronteira_administracao(conn):
    result = run(conn, 2026)
    by_ano = {r["ano"]: r for r in result["restos_pendentes"]}
    assert by_ano[2024]["administracao"] == "Adm. Anterior"
    assert by_ano[2025]["administracao"] == "Adm. Atual"
    assert by_ano[2026]["administracao"] == "Adm. Atual"
