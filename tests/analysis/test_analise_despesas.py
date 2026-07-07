import pytest

import db
from analysis.analise_despesas import (
    get_analise_intensidade_pessoal,
    get_despesas_por_unidade,
    get_impacto_gastos_locais,
    get_impacto_por_ano,
    get_metricas_gerais_despesas,
    get_metricas_por_ano,
    get_perfil_cargos_confianca,
    get_principais_beneficiarios_diarias,
    get_principais_fornecedores_detalhados,
    get_resumo_diarias,
    get_resumo_diarias_por_ano,
    get_transacoes_pesquisaveis,
    total_folha_orgao_por_ano,
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


def test_get_metricas_por_ano(conn):
    result = get_metricas_por_ano(conn, [2026])
    assert 2026 in result
    assert result[2026]["empenhado"] == 15000.0
    assert result[2026]["pago"] == 11000.0


def test_get_impacto_por_ano(conn):
    result = get_impacto_por_ano(conn, [2026])
    assert 2026 in result
    assert result[2026]["local_pago"] == 3000.0
    assert result[2026]["pct_local"] == 60.0


def test_get_resumo_diarias_por_ano(conn):
    result = get_resumo_diarias_por_ano(conn, [2026])
    assert 2026 in result
    assert result[2026]["total_valor"] == 1900.0
    assert result[2026]["total_viajantes"] == 2


def test_total_folha_orgao_por_ano(conn):
    # O fixture não insere registros em despesas_gerais com elemento=11,
    # portanto deve retornar 0 para 2026 sem erro.
    result = total_folha_orgao_por_ano(conn, [2026])
    assert 2026 in result
    assert isinstance(result[2026], float)


def test_get_analise_intensidade_pessoal(conn):
    # Inserir dados de despesas gerais para teste
    import db

    db.upsert(
        conn,
        "despesas_gerais",
        [
            {
                "ano": 2026,
                "empresa": "7",
                "numero": "10",
                "nomeempresa": "Saude",
                "codlo": "1",  # Correspondente ao código da 'Saude' em despesas_por_unidade
                "elemento": "30",
                "pago": "6000",
            },
            {
                "ano": 2026,
                "empresa": "7",
                "numero": "20",
                "nomeempresa": "Saude",
                "codlo": "1",
                "elemento": "11",  # 11 é ELEMENTO_FOLHA_PESSOAL
                "pago": "1000",
            },
        ],
        ["ano", "empresa", "numero"],
    )

    df = get_analise_intensidade_pessoal(conn, [2026])

    assert "orgao" in df.columns
    assert "gasto_total" in df.columns
    assert "gasto_folha" in df.columns
    assert "pct_folha" in df.columns
    assert not df.empty

    # Saude: gasto_total = 6000 (elemento 30) + 1000 (elemento 11) = 7000, gasto_folha = 1000
    saude = df[df["orgao"] == "Saude"].iloc[0]
    assert saude["gasto_total"] == 7000.0
    assert saude["gasto_folha"] == 1000.0
    assert saude["pct_folha"] == pytest.approx(1000 / 7000 * 100, rel=0.01)


def test_get_perfil_cargos_confianca(conn):
    # Inserir dados na tabela pessoal para teste
    import db

    db.upsert(
        conn,
        "pessoal",
        [
            {
                "ano": 2026,
                "empresa": "7",
                "mes": "01",
                "matricula": "M1",
                "vinculo": "Efetivo",
                "categoriafuncional": "Carreira",
                "proventos": "5000",
            },
            {
                "ano": 2026,
                "empresa": "7",
                "mes": "01",
                "matricula": "M2",
                "vinculo": "Comissionado",
                "categoriafuncional": "DAS",
                "proventos": "3000",
            },
            {
                "ano": 2026,
                "empresa": "7",
                "mes": "01",
                "matricula": "M3",
                "vinculo": "Efetivo",
                "categoriafuncional": "DAI",
                "proventos": "2000",
            },
        ],
        ["ano", "empresa", "mes", "matricula"],
    )

    df = get_perfil_cargos_confianca(conn, [2026])

    assert not df.empty
    assert "categoria" in df.columns
    assert "total_provento" in df.columns
    # Verificar categorias
    assert "Servidor Efetivo de Carreira" in df["categoria"].values
    assert "Comissionado Externo Sem Vínculo (Pure DAS)" in df["categoria"].values
    assert "Servidor Efetivo com Função de Confiança (DAI/FG)" in df["categoria"].values
