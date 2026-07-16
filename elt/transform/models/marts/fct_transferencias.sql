-- Fato: transferencias consolidadas de todos os portais

with transferencias as (
    select
        portal_slug,
        ano,
        empresa_id,
        mes,
        entidade_pagadora,
        entidade_recebedora,
        repasse,
        devolucao
    from {{ ref('int_transferencias_consolidadas') }}
)

select
    {{ dbt_utils.generate_surrogate_key(['portal_slug', 'ano', 'empresa_id', 'mes', 'entidade_pagadora', 'entidade_recebedora']) }} as transferencia_id,
    portal_slug,
    ano,
    empresa_id,
    mes,
    entidade_pagadora,
    entidade_recebedora,
    repasse,
    devolucao
from transferencias
