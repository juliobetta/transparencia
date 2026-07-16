-- Dimensão: credores/fornecedores únicos por portal

with base as (
    select
        portal_slug,
        fornecedor_cpf_cnpj,
        fornecedor_nome,
        count(*) as total_empenhos
    from {{ ref('int_despesas_consolidadas') }}
    where fornecedor_nome is not null
    group by portal_slug, fornecedor_cpf_cnpj, fornecedor_nome
),

deduplicado as (
    -- Mantém a ocorrência mais frequente do nome para cada CPF/CNPJ
    select distinct on (portal_slug, fornecedor_cpf_cnpj)
        portal_slug,
        fornecedor_cpf_cnpj,
        fornecedor_nome
    from base
    order by portal_slug, fornecedor_cpf_cnpj, total_empenhos desc
)

select
    {{ dbt_utils.generate_surrogate_key(['portal_slug', 'fornecedor_cpf_cnpj']) }} as credor_id,
    portal_slug,
    fornecedor_cpf_cnpj,
    fornecedor_nome
from deduplicado
