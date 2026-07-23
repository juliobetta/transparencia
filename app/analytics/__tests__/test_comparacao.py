import pandas as pd
import pytest

import db
from app.analytics.comparacao import PeriodSpec, _delta, _filter_months, run


def test_period_spec_fields():
    spec = PeriodSpec(year=2024, mes_inicio=1, mes_fim=6)
    assert spec.year == 2024
    assert spec.mes_inicio == 1
    assert spec.mes_fim == 6


def test_period_spec_invalid_month_range():
    with pytest.raises(ValueError):
        PeriodSpec(year=2024, mes_inicio=6, mes_fim=3)


def test_period_spec_invalid_month_out_of_bounds():
    with pytest.raises(ValueError):
        PeriodSpec(year=2024, mes_inicio=0, mes_fim=12)


def test_delta_normal():
    d = _delta(100.0, 150.0)
    assert d["abs"] == pytest.approx(50.0)
    assert d["pct"] == pytest.approx(50.0)


def test_delta_zero_base():
    d = _delta(0.0, 50.0)
    assert d["pct"] is None


def test_filter_months_filters_correctly():
    df = pd.DataFrame({"mes": ["01", "03", "07", "12"], "val": [1, 2, 3, 4]})
    spec = PeriodSpec(year=2024, mes_inicio=1, mes_fim=6)
    filtered = _filter_months(df, "mes", spec)
    assert len(filtered) == 2
    assert set(filtered["mes"]) == {"01", "03"}


@pytest.fixture
def conn(conn):
    db.upsert(
        conn,
        "despesas_por_orgao",
        [
            {
                "ano": 2024,
                "empresa": "7",
                "codigo": "01",
                "descricao": "SAUDE",
                "empenhado": "100000",
                "liquidado": "90000",
                "pago": "80000",
                "dotac": "200000",
                "altdo": "0",
                "dotacao_atualizada": "200000",
            },
            {
                "ano": 2025,
                "empresa": "7",
                "codigo": "01",
                "descricao": "SAUDE",
                "empenhado": "120000",
                "liquidado": "110000",
                "pago": "100000",
                "dotac": "200000",
                "altdo": "0",
                "dotacao_atualizada": "200000",
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
                "empresa": "7",
                "codigo": "F1",
                "descricao": "FORNECEDOR A",
                "empenhado": "50000",
                "liquidado": "0",
                "pago": "0",
            },
            {
                "ano": 2025,
                "empresa": "7",
                "codigo": "F1",
                "descricao": "FORNECEDOR A",
                "empenhado": "60000",
                "liquidado": "0",
                "pago": "0",
            },
        ],
        ["ano", "empresa", "codigo"],
    )
    db.upsert(
        conn,
        "contratos",
        [
            {
                "ano": 2024,
                "empresa": "7",
                "numero": "C1",
                "fornecedor": "F1",
                "objeto": "X",
                "valor": "10000",
                "licitacao_numero": "",
            },
            {
                "ano": 2025,
                "empresa": "7",
                "numero": "C1",
                "fornecedor": "F1",
                "objeto": "X",
                "valor": "10000",
                "licitacao_numero": "",
            },
            {
                "ano": 2025,
                "empresa": "7",
                "numero": "C2",
                "fornecedor": "F2",
                "objeto": "Y",
                "valor": "80000",
                "licitacao_numero": "",
            },
        ],
        ["ano", "empresa", "numero"],
    )
    db.upsert(
        conn,
        "pessoal",
        [
            {
                "ano": 2024,
                "empresa": "7",
                "mes": "01",
                "matricula": "M1",
                "nome": "A",
                "cargo": "C",
                "proventos": "3000",
            },
            {
                "ano": 2025,
                "empresa": "7",
                "mes": "01",
                "matricula": "M1",
                "nome": "A",
                "cargo": "C",
                "proventos": "3500",
            },
        ],
        ["ano", "empresa", "mes", "matricula"],
    )
    db.upsert(
        conn,
        "receita_orcamentaria",
        [
            {
                "ano": 2024,
                "empresa": "7",
                "codigo": "R1",
                "descricao": "IPTU",
                "previsto": "10000",
                "previsao_atualizada": "10000",
            },
            {
                "ano": 2025,
                "empresa": "7",
                "codigo": "R1",
                "descricao": "IPTU",
                "previsto": "12000",
                "previsao_atualizada": "12000",
            },
        ],
        ["ano", "empresa", "codigo"],
    )
    return conn


def test_run_returns_all_domains(conn):
    spec_a = PeriodSpec(year=2024, mes_inicio=1, mes_fim=12)
    spec_b = PeriodSpec(year=2025, mes_inicio=1, mes_fim=12)
    result = run(conn, spec_a, spec_b)
    assert set(result.keys()) == {
        "spec_a",
        "spec_b",
        "despesas",
        "pessoal",
        "receitas",
        "licitacoes",
        "fornecedores",
        "adesao",
    }


def test_despesas_delta_direction(conn):
    spec_a = PeriodSpec(year=2024, mes_inicio=1, mes_fim=12)
    spec_b = PeriodSpec(year=2025, mes_inicio=1, mes_fim=12)
    result = run(conn, spec_a, spec_b)
    assert result["despesas"]["empenhado"]["b"] > result["despesas"]["empenhado"]["a"]


def test_licitacoes_sem_licitacao_count(conn):
    spec_a = PeriodSpec(year=2024, mes_inicio=1, mes_fim=12)
    spec_b = PeriodSpec(year=2025, mes_inicio=1, mes_fim=12)
    result = run(conn, spec_a, spec_b)
    assert result["licitacoes"]["sem_licitacao"]["a"] == 1
    assert result["licitacoes"]["sem_licitacao"]["b"] == 2


def test_domain_subkeys_match_page_expectations(conn):
    """Ensure every key the dashboard pages access is present in the comparison result."""
    spec_a = PeriodSpec(year=2024, mes_inicio=1, mes_fim=12)
    spec_b = PeriodSpec(year=2025, mes_inicio=1, mes_fim=12)
    result = run(conn, spec_a, spec_b)

    assert {"empenhado", "dotacao"} <= result["despesas"].keys()
    assert {"total_folha", "percentual_folha"} <= result["pessoal"].keys()
    assert {"receita_propria", "transferencias_uniao", "transferencias_estado", "total"} <= result["receitas"].keys()
    assert {"sem_licitacao", "acima_limite", "saude"} <= result["licitacoes"].keys()
    assert {"hhi"} <= result["fornecedores"].keys()
    assert {"quantidade", "valor_licitacao", "valor_contratos"} <= result["adesao"].keys()
