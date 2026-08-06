{{ config(materialized='table') }}

with despesas_fonte as (
    select
        f.portal_slug,
        f.empresa_id,
        f.ano,
        coalesce(f.fornecedor_cpf_cnpj, '00') as fornecedor_codigo,
        coalesce(f.fornecedor_nome, 'OUTROS') as fornecedor_nome,
        coalesce(pf.fornecedor_cidade_clean, 'PORCIUNCULA') as fornecedor_cidade_clean,
        f.empenhado_liquido,
        f.pago
    from {{ ref('fct_despesas') }} f
    left join {{ ref('fct_despesas_por_fornecedor') }} pf
        on pf.ano = f.ano
        and pf.descricao = f.fornecedor_nome
    where f.fonte = 'exercicio'
      and f.elemento in ('30', '36', '39', '52')
),

fornecedores_agregados as (
    select
        portal_slug,
        empresa_id,
        ano,
        fornecedor_codigo,
        fornecedor_nome,
        fornecedor_cidade_clean,
        sum(coalesce(empenhado_liquido, 0)) as total_empenhado,
        sum(coalesce(pago, 0)) as total_pago
    from despesas_fonte
    group by
        portal_slug,
        empresa_id,
        ano,
        fornecedor_codigo,
        fornecedor_nome,
        fornecedor_cidade_clean
)

select
    {{ dbt_utils.generate_surrogate_key(['portal_slug', 'empresa_id', 'ano', 'fornecedor_codigo', 'fornecedor_nome']) }} as fornecedores_metricas_id,
    portal_slug,
    empresa_id,
    ano,
    fornecedor_codigo,
    fornecedor_nome,
    fornecedor_cidade_clean,
    total_empenhado::numeric(15, 2) as total_empenhado,
    total_pago::numeric(15, 2) as total_pago
from fornecedores_agregados
