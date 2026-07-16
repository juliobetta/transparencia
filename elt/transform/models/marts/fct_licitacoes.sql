-- Fato: licitacoes consolidadas de todos os portais

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
    data_abertura,
    carona
from licitacoes
