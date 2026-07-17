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

        # Raw tables that stayed in raw schema — cast financial columns to numeric
        conn.execute(
            text("""
            CREATE OR REPLACE VIEW raw_porciuncula_prefeitura.despesas_por_orgao AS
            SELECT
                empresa, ano, codigo, descricao,
                nullif(replace(empenhado, ',', '.'), '')::numeric AS empenhado,
                nullif(replace(liquidado, ',', '.'), '')::numeric AS liquidado,
                nullif(replace(pago, ',', '.'), '')::numeric AS pago,
                nullif(replace(dotacao_atualizada, ',', '.'), '')::numeric AS dotacao_atualizada
            FROM public.despesas_por_orgao
        """)
        )
        conn.execute(
            text("""
            CREATE OR REPLACE VIEW raw_porciuncula_prefeitura.despesas_por_unidade AS
            SELECT
                empresa, ano, codigo, descricao,
                nullif(replace(empenhado, ',', '.'), '')::numeric AS empenhado,
                nullif(replace(liquidado, ',', '.'), '')::numeric AS liquidado,
                nullif(replace(pago, ',', '.'), '')::numeric AS pago,
                nullif(replace(dotacao_atualizada, ',', '.'), '')::numeric AS dotacao_atualizada
            FROM public.despesas_por_unidade
        """)
        )
        conn.execute(
            text("""
            CREATE OR REPLACE VIEW raw_porciuncula_prefeitura.despesas_por_fornecedor AS
            SELECT
                empresa, ano, codigo, descricao, insmf, cepci,
                nullif(replace(empenhado, ',', '.'), '')::numeric AS empenhado,
                nullif(replace(liquidado, ',', '.'), '')::numeric AS liquidado,
                nullif(replace(pago, ',', '.'), '')::numeric AS pago
            FROM public.despesas_por_fornecedor
        """)
        )

        # fct_despesas_por_* — espelham os modelos dbt intermediários (lêem das views raw já com cast numérico)
        conn.execute(
            text("""
            CREATE OR REPLACE VIEW fct_despesas_por_orgao AS
            SELECT * FROM raw_porciuncula_prefeitura.despesas_por_orgao
        """)
        )
        conn.execute(
            text("""
            CREATE OR REPLACE VIEW fct_despesas_por_unidade AS
            SELECT * FROM raw_porciuncula_prefeitura.despesas_por_unidade
        """)
        )
        conn.execute(
            text("""
            CREATE OR REPLACE VIEW fct_despesas_por_fornecedor AS
            SELECT empresa, ano, codigo, descricao,
                insmf AS fornecedor_cpf_cnpj,
                cepci AS fornecedor_cidade,
                empenhado, liquidado, pago
            FROM raw_porciuncula_prefeitura.despesas_por_fornecedor
        """)
        )

        # fct_despesas — merges despesas_gerais (exercicio) + despesas_restos_pagar (restos_a_pagar)
        # empenhado_liquido replicates dbt logic: empenhado + SUM(anulacoes where pkempa = pkemp)
        conn.execute(
            text("""
                CREATE OR REPLACE VIEW fct_despesas AS
                WITH base AS (
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
                        COALESCE(nullif(replace(empenhado, ',', '.'), '')::numeric, 0) AS empenhado,
                        COALESCE(nullif(replace(liquidado, ',', '.'), '')::numeric, 0) AS liquidado,
                        COALESCE(nullif(replace(pago, ',', '.'), '')::numeric, 0) AS pago,
                        nullif(replace(dotacatualizada, ',', '.'), '')::numeric AS dotacao_atualizada,
                        nullif(replace(dotac, ',', '.'), '')::numeric AS dotacao_inicial,
                        nullif(replace(altdo, ',', '.'), '')::numeric AS alteracao_dotacao
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
                        COALESCE(nullif(replace(empenhado, ',', '.'), '')::numeric, 0) AS empenhado,
                        COALESCE(nullif(replace(liquidado, ',', '.'), '')::numeric, 0) AS liquidado,
                        COALESCE(nullif(replace(pago, ',', '.'), '')::numeric, 0) AS pago,
                        NULL AS dotacao_atualizada,
                        NULL AS dotacao_inicial,
                        NULL AS alteracao_dotacao
                    FROM despesas_restos_pagar
                ),
                anulacoes AS (
                    SELECT pk_empenho_pai, ano, empresa_id, SUM(empenhado) AS total_anulado
                    FROM base
                    WHERE tipo_empenho = 'AN'
                    GROUP BY pk_empenho_pai, ano, empresa_id
                )
                SELECT
                    b.*,
                    b.empenhado + COALESCE(a.total_anulado, 0) AS empenhado_liquido
                FROM base b
                LEFT JOIN anulacoes a
                    ON b.pk_empenho = a.pk_empenho_pai
                    AND b.ano = a.ano
                    AND b.empresa_id = a.empresa_id
                WHERE b.tipo_empenho != 'AN' OR b.tipo_empenho IS NULL
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
                    nullif(replace(valcon, ',', '.'), '')::numeric AS valor_contrato,
                    licitacao_numero,
                    modali AS modalidade,
                    mes,
                    tipocoobra AS tipo_obra,
                    numobra AS numero_obra,
                    COALESCE(nullif(replace(empenhado, ',', '.'), '')::numeric, 0) AS empenhado,
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
                    nullif(replace(valor, ',', '.'), '')::numeric AS valor,
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
                    nullif(replace(valor, ',', '.'), '')::numeric AS valor,
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
                    nullif(replace(proventos, ',', '.'), '')::numeric AS proventos,
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
                    nullif(replace(valor_total, ',', '.'), '')::numeric AS valor_total,
                    COALESCE(nullif(replace(empenhado, ',', '.'), '')::numeric, 0) AS empenhado,
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
                    nullif(replace(repasse, ',', '.'), '')::numeric AS repasse,
                    nullif(replace(devolucao, ',', '.'), '')::numeric AS devolucao
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
                    nullif(replace(previsao_atualizada, ',', '.'), '')::numeric AS previsao_atualizada,
                    COALESCE(nullif(replace(arrecadado_total, ',', '.'), '')::numeric, nullif(replace(arrecadado, ',', '.'), '')::numeric) AS arrecadado
                FROM receita_orcamentaria
                UNION ALL
                SELECT
                    empresa AS empresa_id,
                    ano,
                    'uniao' AS tipo_receita,
                    codigo,
                    descricao,
                    nullif(replace(previsao_atualizada, ',', '.'), '')::numeric AS previsao_atualizada,
                    COALESCE(nullif(replace(arrecadado_total, ',', '.'), '')::numeric, nullif(replace(arrecadado, ',', '.'), '')::numeric) AS arrecadado
                FROM receita_uniao
                UNION ALL
                SELECT
                    empresa AS empresa_id,
                    ano,
                    'estado' AS tipo_receita,
                    codigo,
                    descricao,
                    nullif(replace(previsao_atualizada, ',', '.'), '')::numeric AS previsao_atualizada,
                    COALESCE(nullif(replace(arrecadado_total, ',', '.'), '')::numeric, nullif(replace(arrecadado, ',', '.'), '')::numeric) AS arrecadado
                FROM receita_estado
            """)
        )

        conn.execute(
            text("""
                CREATE OR REPLACE VIEW dim_credor AS
                SELECT DISTINCT ON (insmf)
                    md5(insmf) AS credor_id,
                    'porciuncula_prefeitura' AS portal_slug,
                    insmf AS fornecedor_cpf_cnpj,
                    empresa AS fornecedor_nome,
                    cepci AS fornecedor_cidade
                FROM raw_porciuncula_prefeitura.despesas_por_fornecedor
                WHERE insmf IS NOT NULL
                ORDER BY insmf, ano DESC
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
