import sqlite3
from pathlib import Path

import pytest

import db
from report.generate import generate


@pytest.fixture
def conn():
    c = sqlite3.connect(":memory:")
    c.row_factory = sqlite3.Row
    db.create_tables(c)

    # Budget execution data
    budget_rows = [
        {
            "ano": 2025,
            "empresa": "7",
            "codigo": "01",
            "descricao": "SAUDE",
            "empenhado": "100000",
            "liquidado": "90000",
            "pago": "80000",
            "dotac": "500000",
            "altdo": "0",
            "dotacao_atualizada": "500000",
        },
        {
            "ano": 2025,
            "empresa": "7",
            "codigo": "02",
            "descricao": "EDUCACAO",
            "empenhado": "600000",
            "liquidado": "600000",
            "pago": "600000",
            "dotac": "500000",
            "altdo": "0",
            "dotacao_atualizada": "500000",
        },
    ]
    db.upsert(c, "despesas_por_orgao", budget_rows, ["ano", "empresa", "codigo"])

    # Supplier concentration data
    supplier_rows = [
        {
            "ano": 2025,
            "empresa": "7",
            "codigo": "01",
            "descricao": "ALFA LTDA",
            "empenhado": "600000",
            "liquidado": "0",
            "pago": "0",
        },
        {
            "ano": 2025,
            "empresa": "7",
            "codigo": "02",
            "descricao": "BETA ME",
            "empenhado": "200000",
            "liquidado": "0",
            "pago": "0",
        },
    ]
    db.upsert(c, "despesas_por_fornecedor", supplier_rows, ["ano", "empresa", "codigo"])

    # Bidding gaps data (contracts without bidding)
    bidding_rows = [
        {
            "ano": 2025,
            "empresa": "7",
            "numero": "001",
            "fornecedor": "FORNECEDOR A",
            "objeto": "Serviços gerais",
            "valor": "100000",
            "data_inicio": "2025-01-01",
            "data_fim": "2025-12-31",
            "licitacao_numero": "",  # No bidding
        },
        {
            "ano": 2025,
            "empresa": "7",
            "numero": "002",
            "fornecedor": "FORNECEDOR B",
            "objeto": "Serviços de saúde",
            "valor": "200000",
            "data_inicio": "2025-01-01",
            "data_fim": "2025-12-31",
            "licitacao_numero": "",  # No bidding
        },
    ]
    db.upsert(c, "contratos", bidding_rows, ["ano", "empresa", "numero"])

    # Revenue data
    revenue_rows_2024 = [
        {
            "ano": 2024,
            "empresa": "7",
            "codigo": "01",
            "descricao": "Impostos",
            "previsto": "100000",
            "arrecadado": "100000",
        },
    ]
    revenue_rows_2025 = [
        {
            "ano": 2025,
            "empresa": "7",
            "codigo": "01",
            "descricao": "Impostos",
            "previsto": "150000",
            "arrecadado": "150000",
        },
    ]
    db.upsert(c, "receita_orcamentaria", revenue_rows_2024 + revenue_rows_2025, ["ano", "empresa", "codigo"])

    union_rows = [
        {
            "ano": 2024,
            "empresa": "7",
            "codigo": "01",
            "descricao": "FPM",
            "previsto": "800000",
            "arrecadado": "800000",
        },
        {
            "ano": 2025,
            "empresa": "7",
            "codigo": "01",
            "descricao": "FPM",
            "previsto": "900000",
            "arrecadado": "900000",
        },
    ]
    db.upsert(c, "receita_uniao", union_rows, ["ano", "empresa", "codigo"])

    estado_rows = [
        {
            "ano": 2024,
            "empresa": "7",
            "codigo": "01",
            "descricao": "ICMS",
            "previsto": "50000",
            "arrecadado": "50000",
        },
        {
            "ano": 2025,
            "empresa": "7",
            "codigo": "01",
            "descricao": "ICMS",
            "previsto": "50000",
            "arrecadado": "50000",
        },
    ]
    db.upsert(c, "receita_estado", estado_rows, ["ano", "empresa", "codigo"])

    # Payroll data
    payroll_rows_2024 = [
        {
            "ano": 2024,
            "empresa": "7",
            "mes": "01",
            "matricula": "001",
            "nome": "FUNCIONARIO A",
            "cargo": "GERENTE",
            "remuneracao": "5000",
        },
    ]
    payroll_rows_2025 = [
        {
            "ano": 2025,
            "empresa": "7",
            "mes": "01",
            "matricula": "001",
            "nome": "FUNCIONARIO A",
            "cargo": "GERENTE",
            "remuneracao": "5000",
        },
    ]
    db.upsert(c, "pessoal", payroll_rows_2024 + payroll_rows_2025, ["ano", "empresa", "mes", "matricula"])

    yield c
    c.close()


def test_generate_returns_path(conn, tmp_path):
    # Change to tmp_path so reports are written there
    import os

    old_cwd = os.getcwd()
    try:
        os.chdir(tmp_path)
        result = generate(conn, 2025, 6)
        assert isinstance(result, Path)
        assert result.name == "2025-06.html"
    finally:
        os.chdir(old_cwd)


def test_generate_creates_file(conn, tmp_path):
    import os

    old_cwd = os.getcwd()
    try:
        os.chdir(tmp_path)
        result = generate(conn, 2025, 6)
        assert result.exists()
        assert result.is_file()
    finally:
        os.chdir(old_cwd)


def test_generate_file_contains_html(conn, tmp_path):
    import os

    old_cwd = os.getcwd()
    try:
        os.chdir(tmp_path)
        result = generate(conn, 2025, 6)
        content = result.read_text(encoding="utf-8")
        assert "<!DOCTYPE html>" in content
        assert '<html lang="pt-BR">' in content
        assert "</html>" in content
    finally:
        os.chdir(old_cwd)


def test_generate_includes_portal_url(conn, tmp_path):
    import os

    old_cwd = os.getcwd()
    try:
        os.chdir(tmp_path)
        result = generate(conn, 2025, 6)
        content = result.read_text(encoding="utf-8")
        assert "https://transparencia.porciuncula.rj.gov.br/transparencia/" in content
    finally:
        os.chdir(old_cwd)


def test_generate_includes_glossary_terms(conn, tmp_path):
    import os

    old_cwd = os.getcwd()
    try:
        os.chdir(tmp_path)
        result = generate(conn, 2025, 6)
        content = result.read_text(encoding="utf-8")
        # Check for glossary term definitions
        assert "Dotação Atualizada" in content
        assert "Empenho" in content
        assert "Fornecedor" in content
    finally:
        os.chdir(old_cwd)


def test_generate_includes_budget_data(conn, tmp_path):
    import os

    old_cwd = os.getcwd()
    try:
        os.chdir(tmp_path)
        result = generate(conn, 2025, 6)
        content = result.read_text(encoding="utf-8")
        # Check for budget execution section
        assert "Execução Orçamentária por Órgão" in content
        assert "SAUDE" in content
        assert "EDUCACAO" in content
    finally:
        os.chdir(old_cwd)


def test_generate_includes_supplier_data(conn, tmp_path):
    import os

    old_cwd = os.getcwd()
    try:
        os.chdir(tmp_path)
        result = generate(conn, 2025, 6)
        content = result.read_text(encoding="utf-8")
        # Check for supplier concentration section
        assert "Concentração de Fornecedores" in content
        assert "ALFA LTDA" in content or "BETA ME" in content
    finally:
        os.chdir(old_cwd)


def test_generate_includes_bidding_section(conn, tmp_path):
    import os

    old_cwd = os.getcwd()
    try:
        os.chdir(tmp_path)
        result = generate(conn, 2025, 6)
        content = result.read_text(encoding="utf-8")
        # Check for bidding gaps section
        assert "Contratos sem Licitação" in content
    finally:
        os.chdir(old_cwd)


def test_generate_includes_revenue_section(conn, tmp_path):
    import os

    old_cwd = os.getcwd()
    try:
        os.chdir(tmp_path)
        result = generate(conn, 2025, 6)
        content = result.read_text(encoding="utf-8")
        # Check for revenue section
        assert "Fontes de Receita" in content
    finally:
        os.chdir(old_cwd)


def test_generate_includes_payroll_section(conn, tmp_path):
    import os

    old_cwd = os.getcwd()
    try:
        os.chdir(tmp_path)
        result = generate(conn, 2025, 6)
        content = result.read_text(encoding="utf-8")
        # Check for payroll section
        assert "Folha de Pagamento vs Gastos Totais" in content
    finally:
        os.chdir(old_cwd)


def test_generate_year_month_in_title(conn, tmp_path):
    import os

    old_cwd = os.getcwd()
    try:
        os.chdir(tmp_path)
        result = generate(conn, 2025, 6)
        content = result.read_text(encoding="utf-8")
        # Check for year and month in title
        assert "2025" in content
        assert "06" in content
    finally:
        os.chdir(old_cwd)


def test_generate_outputs_to_reports_yyyy_mm(conn, tmp_path):
    import os

    old_cwd = os.getcwd()
    try:
        os.chdir(tmp_path)
        result = generate(conn, 2023, 3)
        assert result == Path("reports") / "2023-03.html"
    finally:
        os.chdir(old_cwd)
