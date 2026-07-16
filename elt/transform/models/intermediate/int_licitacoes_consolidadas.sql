-- Intermediário: consolida licitacoes de todos os portais via union all.
-- Para adicionar novo portal: incluir novo CTE + union all abaixo.

with porciuncula as (
    select
        'porciuncula_prefeitura' as portal_slug,
        ano,
        empresa_id,
        licitacao_numero,
        modalidade,
        objeto,
        discriminacao,
        valor,
        data_abertura,
        carona
    from {{ ref('stg_porciuncula_prefeitura__licitacoes') }}
)

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
from porciuncula
