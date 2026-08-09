-- Dimensão canônica dos elementos de despesa oficiais (STN/MCASP)
-- Fonte: seed_elemento_despesa

select
    elemento_codigo::text as elemento_codigo,
    elemento_descricao::text as elemento_descricao,
    categoria_macro::text as categoria_macro
from {{ ref('seed_elemento_despesa') }}
