-- Dimensão: entidades municipais (prefeitura + fundos) por portal
-- Fonte: seed porciuncula_prefeitura_orgaos (e futuros seeds de novos portais)

select
    {{ dbt_utils.generate_surrogate_key(['portal_slug', 'empresa_id']) }} as orgao_id,
    portal_slug,
    empresa_id::text as empresa_id,
    nome as orgao_nome
from {{ ref('porciuncula_prefeitura_orgaos') }}
