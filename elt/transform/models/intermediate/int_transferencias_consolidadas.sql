-- Intermediário: consolida transferencias de todos os portais via union all.
-- Para adicionar novo portal: incluir novo CTE + union all abaixo.

with porciuncula as (
    select
        'porciuncula_prefeitura' as portal_slug,
        ano,
        empresa_id,
        mes,
        entidade_pagadora,
        entidade_recebedora,
        repasse,
        devolucao
    from {{ ref('stg_porciuncula_prefeitura__transferencias') }}
)

select
    portal_slug,
    ano,
    empresa_id,
    mes,
    entidade_pagadora,
    entidade_recebedora,
    repasse,
    devolucao
from porciuncula
