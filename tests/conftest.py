import os
import sys
from pathlib import Path

import pytest
import testing.postgresql
from sqlalchemy import text
from sqlalchemy.engine import Connection
from sqlmodel import SQLModel, create_engine

sys.path.insert(0, str(Path(__file__).parent.parent))

os.environ.setdefault("PORTAL_SLUG", "porciuncula_prefeitura")

import models  # noqa: F401 — registers all tables in SQLModel.metadata


def _create_test_views(eng) -> None:
    """Create raw schema + fct_* views so analysis/ queries work against test DB.

    The test fixtures insert data into the original SQLModel tables (public schema).
    These views expose that same data under the names the migrated analysis code expects.
    """
    with eng.connect() as conn:
        conn.execute(text("CREATE SCHEMA IF NOT EXISTS raw_porciuncula_prefeitura"))

        # Raw tables that stayed in raw schema — simple pass-through views
        for tbl in ("despesas_por_orgao", "despesas_por_unidade", "despesas_por_fornecedor"):
            conn.execute(text(f"CREATE OR REPLACE VIEW raw_porciuncula_prefeitura.{tbl} AS SELECT * FROM public.{tbl}"))

        # fct_despesas — merges despesas_gerais (exercicio) + despesas_restos_pagar (restos_a_pagar)
        conn.execute(
            text("""
                CREATE OR REPLACE VIEW fct_despesas AS
                SELECT
                    empresa AS empresa_id,
                    'exercicio' AS fonte,
                    ano,
                    numero AS empenho_id,
                    pkemp AS pk_empenho,
                    pkempa AS pk_empenho_pai,
                    tpem AS tipo_empenho,
                    orgao AS orgao_codigo,
                    nomefor AS fornecedor_nome,
                    cpfformatado AS fornecedor_cpf_cnpj,
                    datae AS data_empenho,
                    produ AS descricao,
                    numlicit AS licitacao_numero,
                    licit AS licitacao_modalidade,
                    funcao,
                    funcaonome AS funcao_nome,
                    subfuncao,
                    subfuncaonome AS subfuncao_nome,
                    natureza AS natureza_despesa,
                    projativ AS proj_atividade,
                    gruponatureza AS grupo_natureza,
                    programa,
                    programanome AS programa_nome,
                    elemento,
                    mes,
                    nomeempresa AS empresa_nome,
                    COALESCE(NULLIF(empenhado, ''), '0') AS empenhado,
                    COALESCE(NULLIF(liquidado, ''), '0') AS liquidado,
                    COALESCE(NULLIF(pago, ''), '0') AS pago,
                    dotacatualizada AS dotacao_atualizada,
                    dotac AS dotacao_inicial,
                    altdo AS alteracao_dotacao
                FROM despesas_gerais
                UNION ALL
                SELECT
                    empresa AS empresa_id,
                    'restos_a_pagar' AS fonte,
                    ano,
                    numero AS empenho_id,
                    NULL AS pk_empenho,
                    NULL AS pk_empenho_pai,
                    NULL AS tipo_empenho,
                    NULL AS orgao_codigo,
                    NULL AS fornecedor_nome,
                    NULL AS fornecedor_cpf_cnpj,
                    NULL AS data_empenho,
                    NULL AS empresa_nome,
                    descricao,
                    NULL AS licitacao_numero,
                    NULL AS licitacao_modalidade,
                    NULL AS funcao,
                    NULL AS funcao_nome,
                    NULL AS subfuncao,
                    NULL AS subfuncao_nome,
                    NULL AS natureza_despesa,
                    NULL AS proj_atividade,
                    NULL AS grupo_natureza,
                    NULL AS programa,
                    NULL AS programa_nome,
                    NULL AS elemento,
                    NULL AS mes,
                    COALESCE(NULLIF(empenhado, ''), '0') AS empenhado,
                    COALESCE(NULLIF(liquidado, ''), '0') AS liquidado,
                    COALESCE(NULLIF(pago, ''), '0') AS pago,
                    NULL AS dotacao_atualizada,
                    NULL AS dotacao_inicial,
                    NULL AS alteracao_dotacao
                FROM despesas_restos_pagar
            """)
        )

        # fct_contratos — column renames from contratos
        conn.execute(
            text("""
                CREATE OR REPLACE VIEW fct_contratos AS
                SELECT
                    empresa AS empresa_id,
                    ano,
                    numero AS contrato_numero,
                    fornecedor AS fornecedor_nome,
                    objeto,
                    valcon AS valor_contrato,
                    licitacao_numero,
                    modali AS modalidade,
                    mes,
                    tipocoobra AS tipo_obra,
                    numobra AS numero_obra,
                    empenhado,
                    fundlegal
                FROM contratos
            """)
        )

        # fct_licitacoes — column renames from licitacoes
        conn.execute(
            text("""
                CREATE OR REPLACE VIEW fct_licitacoes AS
                SELECT
                    empresa AS empresa_id,
                    ano,
                    numero AS licitacao_numero,
                    modalidade,
                    objeto,
                    discr AS discriminacao,
                    valor,
                    situacao,
                    data_abertura,
                    carona
                FROM licitacoes
            """)
        )

        # fct_diarias — column renames from diarias
        conn.execute(
            text("""
                CREATE OR REPLACE VIEW fct_diarias AS
                SELECT
                    empresa AS empresa_id,
                    ano,
                    numero AS diaria_id,
                    valor,
                    favorecido,
                    cargo,
                    data,
                    unidade,
                    descricao
                FROM diarias
            """)
        )

        # fct_pessoal — column renames from pessoal
        conn.execute(
            text("""
                CREATE OR REPLACE VIEW fct_pessoal AS
                SELECT
                    empresa AS empresa_id,
                    ano,
                    proventos,
                    categoriafuncional AS categoria_funcional,
                    vinculo,
                    cargo,
                    formaprovimento AS forma_provimento
                FROM pessoal
            """)
        )

        # fct_emendas — column renames from emendas_cad
        conn.execute(
            text("""
                CREATE OR REPLACE VIEW fct_emendas AS
                SELECT
                    empresa AS empresa_id,
                    ano,
                    numero_emenda,
                    resumo,
                    valor_total,
                    empenhado,
                    autor,
                    tipo_emenda_descr AS tipo_emenda,
                    esfera_origem,
                    ato_normativo,
                    destinacao_descr AS destinacao
                FROM emendas_cad
            """)
        )

        # fct_transferencias — column rename from transferencias
        conn.execute(
            text("""
                CREATE OR REPLACE VIEW fct_transferencias AS
                SELECT
                    empresa AS empresa_id,
                    ano,
                    mes,
                    entidade_pagadora,
                    entidade_recebedora,
                    repasse,
                    devolucao
                FROM transferencias
            """)
        )

        # fct_receitas — union of three raw receita tables
        conn.execute(
            text("""
                CREATE OR REPLACE VIEW fct_receitas AS
                SELECT
                    empresa AS empresa_id,
                    ano,
                    'orcamentaria' AS tipo_receita,
                    codigo,
                    descricao,
                    previsao_atualizada,
                    COALESCE(arrecadado_total, arrecadado) AS arrecadado
                FROM receita_orcamentaria
                UNION ALL
                SELECT
                    empresa AS empresa_id,
                    ano,
                    'uniao' AS tipo_receita,
                    codigo,
                    descricao,
                    previsao_atualizada,
                    COALESCE(arrecadado_total, arrecadado) AS arrecadado
                FROM receita_uniao
                UNION ALL
                SELECT
                    empresa AS empresa_id,
                    ano,
                    'estado' AS tipo_receita,
                    codigo,
                    descricao,
                    previsao_atualizada,
                    COALESCE(arrecadado_total, arrecadado) AS arrecadado
                FROM receita_estado
            """)
        )

        conn.execute(
            text("""
                CREATE OR REPLACE VIEW dim_metadata AS
                SELECT portal_slug, key, value
                FROM metadata
            """)
        )

        conn.commit()


@pytest.fixture(scope="session")
def pg():
    with testing.postgresql.Postgresql() as pg:
        yield pg


@pytest.fixture(scope="session")
def engine(pg):
    eng = create_engine(pg.url())
    SQLModel.metadata.create_all(eng)
    _create_test_views(eng)
    return eng


@pytest.fixture
def conn(engine) -> Connection:
    with engine.connect() as connection:
        yield connection
        connection.rollback()
