from pathlib import Path

import pytest

import db
from report.generate import generate


@pytest.fixture
def populated_conn(conn):
    db.upsert(
        conn,
        "despesas_por_orgao",
        [
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
        ],
        ["ano", "empresa", "codigo"],
    )
    db.upsert(
        conn,
        "despesas_por_fornecedor",
        [
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
        ],
        ["ano", "empresa", "codigo"],
    )
    db.upsert(
        conn,
        "contratos",
        [
            {
                "ano": 2025,
                "empresa": "7",
                "numero": "001",
                "fornecedor": "FORNECEDOR A",
                "objeto": "Serviços gerais",
                "valor": "100000",
                "data_inicio": "2025-01-01",
                "data_fim": "2025-12-31",
                "licitacao_numero": "",
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
                "licitacao_numero": "",
            },
        ],
        ["ano", "empresa", "numero"],
    )
    db.upsert(
        conn,
        "receita_orcamentaria",
        [
            {
                "ano": 2024,
                "empresa": "7",
                "codigo": "01",
                "descricao": "Impostos",
                "previsto": "100000",
                "arrecadado": "100000",
            },
            {
                "ano": 2025,
                "empresa": "7",
                "codigo": "01",
                "descricao": "Impostos",
                "previsto": "150000",
                "arrecadado": "150000",
            },
        ],
        ["ano", "empresa", "codigo"],
    )
    db.upsert(
        conn,
        "receita_uniao",
        [
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
        ],
        ["ano", "empresa", "codigo"],
    )
    db.upsert(
        conn,
        "receita_estado",
        [
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
                "nome": "FUNCIONARIO A",
                "cargo": "GERENTE",
                "remuneracao": "5000",
            },
            {
                "ano": 2025,
                "empresa": "7",
                "mes": "01",
                "matricula": "001",
                "nome": "FUNCIONARIO A",
                "cargo": "GERENTE",
                "remuneracao": "5000",
            },
        ],
        ["ano", "empresa", "mes", "matricula"],
    )
    db.upsert(
        conn,
        "despesas_restos_pagar",
        [
            {
                "ano": 2024,
                "empresa": "7",
                "numero": "001",
                "descricao": "Restos 2024",
                "fornecedor": "VARIO",
                "valor": "10000",
                "situacao": "pendente",
            },
            {
                "ano": 2025,
                "empresa": "7",
                "numero": "002",
                "descricao": "Restos 2025",
                "fornecedor": "VARIO",
                "valor": "15000",
                "situacao": "pendente",
            },
        ],
        ["ano", "empresa", "numero"],
    )
    return conn


def test_generate_returns_path(populated_conn, tmp_path):
    import os

    old_cwd = os.getcwd()
    try:
        os.chdir(tmp_path)
        result = generate(populated_conn, 2025, 6)
        assert isinstance(result, Path)
        assert result.name == "2025-06.html"
    finally:
        os.chdir(old_cwd)


def test_generate_creates_file(populated_conn, tmp_path):
    import os

    old_cwd = os.getcwd()
    try:
        os.chdir(tmp_path)
        result = generate(populated_conn, 2025, 6)
        assert result.exists()
        assert result.is_file()
    finally:
        os.chdir(old_cwd)


def test_generate_file_contains_html(populated_conn, tmp_path):
    import os

    old_cwd = os.getcwd()
    try:
        os.chdir(tmp_path)
        result = generate(populated_conn, 2025, 6)
        content = result.read_text(encoding="utf-8")
        assert "<!DOCTYPE html>" in content
        assert '<html lang="pt-BR">' in content
        assert "</html>" in content
    finally:
        os.chdir(old_cwd)


def test_generate_includes_budget_data(populated_conn, tmp_path):
    import os

    old_cwd = os.getcwd()
    try:
        os.chdir(tmp_path)
        result = generate(populated_conn, 2025, 6)
        content = result.read_text(encoding="utf-8")
        assert "SAUDE" in content
        assert "EDUCACAO" in content
    finally:
        os.chdir(old_cwd)


def test_generate_includes_supplier_data(populated_conn, tmp_path):
    import os

    old_cwd = os.getcwd()
    try:
        os.chdir(tmp_path)
        result = generate(populated_conn, 2025, 6)
        content = result.read_text(encoding="utf-8")
        assert "ALFA LTDA" in content or "BETA ME" in content
    finally:
        os.chdir(old_cwd)


def test_generate_outputs_to_reports_yyyy_mm(populated_conn, tmp_path):
    import os

    old_cwd = os.getcwd()
    try:
        os.chdir(tmp_path)
        result = generate(populated_conn, 2023, 3)
        assert result == Path("reports") / "2023-03.html"
    finally:
        os.chdir(old_cwd)
