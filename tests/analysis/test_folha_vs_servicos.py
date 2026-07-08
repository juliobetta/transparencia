import pytest

import db
from analysis.folha_vs_servicos import run


@pytest.fixture
def conn(conn):
    db.upsert(
        conn,
        "receita_orcamentaria",
        [
            {
                "ano": 2024,
                "empresa": "1",
                "codigo": "1.1",
                "arrecadado": "1200000",
            },
        ],
        ["ano", "empresa", "codigo"],
    )
    db.upsert(
        conn,
        "despesas_por_orgao",
        [
            {
                "ano": 2024,
                "empresa": "7",
                "codigo": "01",
                "descricao": "SAUDE",
                "empenhado": "1000000",
                "liquidado": "900000",
                "pago": "800000",
                "dotac": "1000000",
                "altdo": "0",
                "dotacao_atualizada": "1000000",
            },
        ],
        ["ano", "empresa", "codigo"],
    )
    db.upsert(
        conn,
        "pessoal",
        [
            {
                "ano": 2024,
                "empresa": "7",
                "mes": "01",
                "matricula": "001",
                "nome": "JOAO",
                "cargo": "AGENTE",
                "proventos": "300000",
            },
            {
                "ano": 2024,
                "empresa": "7",
                "mes": "02",
                "matricula": "001",
                "nome": "JOAO",
                "cargo": "AGENTE",
                "proventos": "300000",
            },
        ],
        ["ano", "empresa", "mes", "matricula"],
    )
    return conn


def test_returns_dataframe_with_percentual(conn):
    df = run(conn, [2024])
    assert "percentual_folha" in df.columns
    row = df[df["ano"] == 2024].iloc[0]
    assert row["total_folha"] == pytest.approx(600000, rel=0.01)
    assert row["total_pago"] == pytest.approx(800000, rel=0.01)
    assert row["rcl_proxy"] == pytest.approx(1200000, rel=0.01)
    # percentual_folha = 600000 / 1200000 * 100 = 50%
    assert row["percentual_folha"] == pytest.approx(50.0, rel=0.01)


def test_execucao_decimo_terceiro(conn):
    from analysis.folha_vs_servicos import execucao_decimo_terceiro

    db.upsert(
        conn,
        "despesas_gerais",
        [
            {
                "ano": 2024,
                "empresa": "7",
                "numero": "123",
                "elemento": "11",
                "produ": "PAGAMENTO DE 13º SALÁRIO",
                "empenhado": "1000,00",
                "anulado": "-100,00",
                "liquidado": "900,00",
                "pago": "800,00",
                "tpem": "ES",
            }
        ],
        ["ano", "empresa", "numero"],
    )

    result = execucao_decimo_terceiro(conn, 2024)
    assert result is not None
    assert result["empenhado"] == 900.0
    assert result["empenhado_bruto"] == 1000.0
    assert result["liquidado"] == 900.0
    assert result["pago"] == 800.0
    assert result["pct_pago"] == pytest.approx(800.0 / 900.0)


def test_execucao_decimo_terceiro_empty(conn):
    from analysis.folha_vs_servicos import execucao_decimo_terceiro

    result = execucao_decimo_terceiro(conn, 2025)
    assert result is None


def test_detalhe_decimo_terceiro(conn):
    from analysis.folha_vs_servicos import detalhe_decimo_terceiro

    db.upsert(
        conn,
        "despesas_gerais",
        [
            {
                "ano": 2024,
                "empresa": "7",
                "numero": "123",
                "elemento": "11",
                "nomeempresa": "PREFEITURA MUNICIPAL DE PORCIÚNCULA",
                "funcaonome": "Administração",
                "produ": "PAGAMENTO DE 13º SALÁRIO",
                "empenhado": "1000,00",
                "anulado": "-100,00",
                "liquidado": "900,00",
                "pago": "800,00",
                "tpem": "ES",
            }
        ],
        ["ano", "empresa", "numero"],
    )

    df = detalhe_decimo_terceiro(conn, 2024)
    assert not df.empty
    row = df.iloc[0]
    assert row["orgao"] == "PREFEITURA MUNICIPAL DE PORCIÚNCULA"
    assert row["funcao"] == "Administração"
    assert row["empenhado"] == 900.0
    assert row["liquidado"] == 900.0
    assert row["pago"] == 800.0
    assert row["pct_pago"] == pytest.approx(800.0 / 900.0 * 100.0)


def test_detalhe_decimo_terceiro_empty(conn):
    from analysis.folha_vs_servicos import detalhe_decimo_terceiro

    df = detalhe_decimo_terceiro(conn, 2025)
    assert df.empty
    assert list(df.columns) == ["orgao", "funcao", "empenhado", "liquidado", "pago", "pct_pago"]
