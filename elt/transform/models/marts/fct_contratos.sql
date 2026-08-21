{{ config(
    post_hook=[
        "{% if not var('test_mode', false) %} CREATE INDEX IF NOT EXISTS idx_fct_contratos_fornecedor_unaccent ON {{ this }} (immutable_unaccent(lower(fornecedor_nome))) {% endif %}",
        "{% if not var('test_mode', false) %} CREATE INDEX IF NOT EXISTS idx_fct_contratos_objeto_trgm ON {{ this }} USING gin (immutable_unaccent(lower(objeto)) gin_trgm_ops) {% endif %}"
    ]
) }}

with contratos as (
    select
        portal_slug,
        ano,
        empresa_id,
        contrato_numero,
        fornecedor_nome,
        fornecedor_cpf_cnpj,
        objeto,
        objeto_completo,
        valor_contrato,
        valor_aditado,
        licitacao_numero,
        modalidade,
        mes,
        tipo_obra,
        numero_obra,
        fundlegal,
        empenhado,
        data_inicio,
        vencimento_atual,
        saldo_a_empenhar
    from {{ ref('int_contratos_consolidados') }}
)

select
    {{ dbt_utils.generate_surrogate_key(['portal_slug', 'ano', 'empresa_id', 'contrato_numero']) }} as contrato_id,
    portal_slug,
    ano,
    empresa_id,
    contrato_numero,
    fornecedor_nome,
    fornecedor_cpf_cnpj,
    objeto,
    objeto_completo,
    valor_contrato,
    valor_aditado,
    licitacao_numero,
    modalidade,
    mes,
    tipo_obra,
    numero_obra,
    fundlegal,
    empenhado,
    data_inicio,
    vencimento_atual,
    saldo_a_empenhar
from contratos
