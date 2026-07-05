import pytest

import db
from analysis.historia_saude import run

SAUDE = "2"
OTHER = "7"


@pytest.fixture
def conn(conn):
    db.upsert(
        conn,
        "emendas_cad",
        [
            {
                "ano": 2023,
                "empresa": SAUDE,
                "numero": "E001",
                "numero_emenda": "E001",
                "resumo": "MEDICAMENTOS",
                "valor_total": "500000",
                "empenhado": "400000",
                "autor": "Deputado X",
                "tipo_emenda_descr": "Individual",
                "esfera_origem": "Federal",
                "ato_normativo": "123",
                "destinacao_descr": "Saúde",
            },
            {
                "ano": 2023,
                "empresa": OTHER,
                "numero": "E002",
                "numero_emenda": "E002",
                "resumo": "OBRAS",
                "valor_total": "1000000",
                "empenhado": "0",
                "autor": "Deputado Y",
                "tipo_emenda_descr": "Individual",
                "esfera_origem": "Federal",
                "ato_normativo": "456",
                "destinacao_descr": "Infra",
            },
        ],
        ["ano", "empresa", "numero"],
    )
    db.upsert(
        conn,
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
        conn,
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
                "discr": "REMÉDIOS",
            },
            {
                "ano": 2023,
                "empresa": SAUDE,
                "numero": "L002",
                "modalidade": "PREGÃO ELETRÔNICO",
                "objeto": "CARONA",
                "valor": "150000",
                "carona": "S",
                "discr": "CARONA",
            },
        ],
        ["ano", "empresa", "numero"],
    )
    db.upsert(
        conn,
        "contratos",
        [
            {
                "ano": 2023,
                "empresa": SAUDE,
                "numero": "C001",
                "fornecedor": "ALFA",
                "objeto": "REMÉDIOS",
                "valor": "200000",
                "valcon": "200000",
                "empenhado": "200000",
                "licitacao_numero": "L001",
                "modali": "PREGÃO ELETRÔNICO",
                "mes": "01",
            },
            {
                "ano": 2023,
                "empresa": SAUDE,
                "numero": "C002",
                "fornecedor": "BETA",
                "objeto": "MATERIAL",
                "valor": "100000",
                "valcon": "100000",
                "empenhado": "100000",
                "licitacao_numero": "",
                "modali": "DISPENSA",
                "mes": "02",
            },
            {
                "ano": 2023,
                "empresa": SAUDE,
                "numero": "C003",
                "fornecedor": "GAMA",
                "objeto": "CARONA",
                "valor": "150000",
                "valcon": "150000",
                "empenhado": "150000",
                "licitacao_numero": "L002",
                "modali": "PREGÃO ELETRÔNICO",
                "mes": "03",
            },
            {
                "ano": 2023,
                "empresa": OTHER,
                "numero": "C004",
                "fornecedor": "DELTA",
                "objeto": "OBRA",
                "valor": "500000",
                "valcon": "500000",
                "empenhado": "500000",
                "licitacao_numero": "L003",
                "modali": "PREGÃO PRESENCIAL",
                "mes": "04",
            },
        ],
        ["ano", "empresa", "numero"],
    )
    db.upsert(
        conn,
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
    db.upsert(
        conn,
        "despesas_gerais",
        [
            {
                "ano": 2023,
                "empresa": SAUDE,
                "numero": "DG001",
                "nomefor": "ALFA LTDA",
                "elemento": "39",
                "empenhado": "500000",
            },
            {
                "ano": 2023,
                "empresa": SAUDE,
                "numero": "DG002",
                "nomefor": "BETA ME",
                "elemento": "30",
                "empenhado": "300000",
            },
        ],
        ["ano", "empresa", "numero"],
    )
    return conn


def test_emendas_filtradas_por_empresa(conn):
    result = run(conn, 2023)
    assert len(result["emendas"]) == 1
    assert result["emendas"].iloc[0]["Nº"] == "E001"


def test_emendas_total(conn):
    result = run(conn, 2023)
    assert result["emendas_total"] == 500000.0


def test_orcamento_filtrado_por_empresa(conn):
    result = run(conn, 2023)
    assert result["orcamento"]["dotacao"] == 1_000_000.0
    assert result["orcamento"]["empenhado"] == 800_000.0


def test_orcamento_taxa_execucao(conn):
    result = run(conn, 2023)
    assert abs(result["orcamento"]["taxa_execucao"] - 0.8) < 0.001


def test_tendencia_execucao_filtrada_por_empresa(conn):
    result = run(conn, 2023)
    trend = result["tendencia_execucao"]
    assert set(trend["ano"].tolist()) == {2022, 2023}
    row_2023 = trend[trend["ano"] == 2023].iloc[0]
    assert row_2023["empenhado"] == 800_000.0


def test_adesao_de_ata_detectada(conn):
    result = run(conn, 2023)
    assert result["adesao_de_ata_count"] == 1
    assert result["adesao_de_ata_value"] == 150_000.0


def test_licitacao_gaps_acima_do_limite(conn):
    result = run(conn, 2023)
    assert len(result["licitacao_gaps"]) == 1
    assert result["licitacao_gaps"].iloc[0]["numero"] == "C002"


def test_licitacao_gaps_tem_coluna_isento_legalmente(conn):
    result = run(conn, 2023)
    assert "isento_legalmente" in result["licitacao_gaps"].columns


def test_licitacao_gaps_dispensa_nao_isento(conn):
    result = run(conn, 2023)
    # C002 tem modali="DISPENSA" — não deve ser isento legalmente
    gap = result["licitacao_gaps"].iloc[0]
    assert gap["isento_legalmente"] is False or gap["isento_legalmente"] == False  # noqa: E712


def test_licitacao_gaps_consorcio_e_rateio_sao_isentos(conn):
    import db

    db.upsert(
        conn,
        "contratos",
        [
            {
                "ano": 2023,
                "empresa": SAUDE,
                "numero": "C006",
                "fornecedor": "CODESP - CONSÓRCIO INTERMUNICIPAL PARA DESENVOLVIM",
                "objeto": "CONT. PROGRAMA PARA EXECUSÃO DE AÇÕES NO CAPS",
                "valor": "300000",
                "valcon": "300000",
                "empenhado": "300000",
                "licitacao_numero": "",
                "modali": "DISPENSA",
                "mes": "06",
            },
            {
                "ano": 2023,
                "empresa": SAUDE,
                "numero": "C007",
                "fornecedor": "MUNICIPIO DE XYZ",
                "objeto": "CONTRATO DE RATEIO",
                "valor": "150000",
                "valcon": "150000",
                "empenhado": "150000",
                "licitacao_numero": "",
                "modali": "OUTRO NAO APLICAVEL",
                "mes": "07",
            },
        ],
        ["ano", "empresa", "numero"],
    )
    result = run(conn, 2023)
    gaps = result["licitacao_gaps"]
    assert gaps[gaps["numero"] == "C006"].iloc[0]["isento_legalmente"] == True  # noqa: E712
    assert gaps[gaps["numero"] == "C007"].iloc[0]["isento_legalmente"] == True  # noqa: E712


def test_licitacao_gaps_inexigibilidade_e_isento(conn):
    import db

    db.upsert(
        conn,
        "contratos",
        [
            {
                "ano": 2023,
                "empresa": SAUDE,
                "numero": "C005",
                "fornecedor": "ESPECIALISTA SA",
                "objeto": "SERVICO ESPECIALIZADO",
                "valor": "200000",
                "valcon": "200000",
                "empenhado": "200000",
                "licitacao_numero": "",
                "modali": "Inexigibilidade de Licitação",
                "mes": "05",
            }
        ],
        ["ano", "empresa", "numero"],
    )
    result = run(conn, 2023)
    gaps = result["licitacao_gaps"]
    c005 = gaps[gaps["numero"] == "C005"]
    assert len(c005) == 1
    assert c005.iloc[0]["isento_legalmente"] is True or c005.iloc[0]["isento_legalmente"] == True  # noqa: E712


def test_principais_fornecedores_filtrados_por_empresa(conn):
    result = run(conn, 2023)
    names = result["principais_fornecedores"]["descricao"].tolist()
    assert "DELTA SA" not in names
    assert "ALFA LTDA" in names


def test_hhi_positivo(conn):
    result = run(conn, 2023)
    assert result["hhi"] > 0
