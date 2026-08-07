{{ config(materialized='table') }}

with caprem_despesas as (
    select
        d.portal_slug,
        d.ano,
        coalesce(d.empenho_id, '') as empenho_id,
        coalesce(d.elemento, '') as elemento,
        coalesce(dim.elemento_descricao, d.natureza_despesa, '') as natureza_despesa,
        d.fornecedor_nome,
        d.descricao,
        d.data_empenho,
        case
            when d.fornecedor_nome ilike '%CASP%' or d.descricao ilike '%CASP%' or d.natureza_despesa ilike '%CASP%' or d.fornecedor_cpf_cnpj = '07.573.075/0001-00' then 'plano_saude_casp'
            when d.elemento = '97' then 'aporte_atuarial_caprem'
            when d.elemento = '71' then 'amortizacao_divida_caprem'
            when d.natureza_despesa ilike '%INSS%' or d.natureza_despesa ilike '%RGPS%' then 'inss_rgps'
            when d.elemento = '13' or d.fornecedor_nome ilike '%CAPREM%' or d.descricao ilike '%CAPREM%' then 'rpps_caprem'
            else 'encargo_patronal_geral'
        end as destino,
        coalesce(d.empenhado_liquido, 0) as empenhado,
        coalesce(d.liquidado, 0) as liquidado,
        coalesce(d.pago, 0) as pago
    from {{ ref('fct_despesas') }} d
    left join {{ ref('dim_elemento_despesa') }} dim
        on d.elemento = dim.elemento_codigo
    where
        d.fonte = 'exercicio'
        and (
            d.elemento in ('13', '71', '97')
            or d.orgao_codigo = '1061'
            or d.credor_id = '1061'
            or d.fornecedor_nome ilike '%CAPREM%'
            or d.fornecedor_nome ilike '%CASP%'
            or d.fornecedor_cpf_cnpj = '07.573.075/0001-00'
            or d.descricao ilike '%CAPREM%'
            or d.descricao ilike '%CASP%'
        )
        and (d.tipo_empenho is null or d.tipo_empenho != 'AN')
),

agregado as (
    select
        portal_slug,
        ano,
        empenho_id,
        elemento,
        natureza_despesa,
        destino,
        max(descricao) as descricao,
        max(data_empenho) as data_empenho,
        sum(empenhado) as empenhado,
        sum(liquidado) as liquidado,
        sum(pago) as pago
    from caprem_despesas
    group by
        portal_slug,
        ano,
        empenho_id,
        elemento,
        natureza_despesa,
        destino
)

select
    {{ dbt_utils.generate_surrogate_key(['portal_slug', 'ano', 'empenho_id', 'elemento', 'natureza_despesa', 'destino']) }} as caprem_natureza_id,
    portal_slug,
    ano,
    empenho_id,
    elemento,
    natureza_despesa,
    destino,
    descricao,
    data_empenho,
    empenhado::numeric(15, 2) as empenhado,
    liquidado::numeric(15, 2) as liquidado,
    pago::numeric(15, 2) as pago
from agregado
