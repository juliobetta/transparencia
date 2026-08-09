-- Dimensão canônica de Natureza de Despesa (Portaria STN/SOF nº 163/2001)
-- Fonte: seed_natureza_despesa

select
    natureza_despesa_codigo::text as natureza_despesa_codigo,
    categoria_economica_codigo::text as categoria_economica_codigo,
    categoria_economica_nome::text as categoria_economica_nome,
    gnd_codigo::text as gnd_codigo,
    gnd_nome::text as gnd_nome,
    modalidade_codigo::text as modalidade_codigo,
    modalidade_nome::text as modalidade_nome
from {{ ref('seed_natureza_despesa') }}
