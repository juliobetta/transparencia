{{ config(
    post_hook=[
        "{% if not var('test_mode', false) %} CREATE INDEX IF NOT EXISTS idx_fct_licitacoes_objeto_unaccent ON {{ this }} (immutable_unaccent(lower(objeto))) {% endif %}"
    ]
) }}

with licitacoes as (
    select
        portal_slug,
        ano,
        empresa_id,
        licitacao_numero,
        modalidade,
        objeto,
        discriminacao,
        valor,
        situacao,
        data_abertura,
        carona
    from {{ ref('int_licitacoes_consolidadas') }}
)

select
    {{ dbt_utils.generate_surrogate_key(['portal_slug', 'ano', 'empresa_id', 'licitacao_numero']) }} as licitacao_id,
    portal_slug,
    ano,
    empresa_id,
    licitacao_numero,
    modalidade,
    objeto,
    discriminacao,
    valor,
    situacao,
    data_abertura,
    carona
from licitacoes
