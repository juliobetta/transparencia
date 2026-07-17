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
),

cidades as (
    -- Cidade do fornecedor: disponível apenas na tabela pré-agregada do portal
    select distinct on (insmf)
        insmf as fornecedor_cpf_cnpj,
        cepci as fornecedor_cidade
    from {{ source('porciuncula_prefeitura', 'despesas_por_fornecedor') }}
    where insmf is not null
    order by insmf, ano desc
),

final as (
    select
        d.portal_slug,
        d.fornecedor_cpf_cnpj,
        d.fornecedor_nome,
        c.fornecedor_cidade
    from deduplicado d
    left join cidades c on d.fornecedor_cpf_cnpj = c.fornecedor_cpf_cnpj
)

select
    {{ dbt_utils.generate_surrogate_key(['portal_slug', 'fornecedor_cpf_cnpj']) }} as credor_id,
    portal_slug,
    fornecedor_cpf_cnpj,
    fornecedor_nome,
    fornecedor_cidade
from final
