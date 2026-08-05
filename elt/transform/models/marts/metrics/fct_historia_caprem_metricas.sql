{{ config(materialized='table') }}

with despesas_caprem as (
    select
        d.portal_slug,
        d.ano,
        sum(case when d.elemento = '97' then coalesce(d.empenhado_liquido, 0) else 0 end) as total_aporte_exigido,
        sum(case when d.elemento = '97' then coalesce(d.pago, 0) else 0 end) as total_aporte_quitado,
        sum(
            case
                when d.elemento = '13' and (d.fornecedor_nome ilike '%CAPREM%' or d.natureza_despesa ilike '%RPPS%' or d.natureza_despesa ilike '%CAPREM%' or d.descricao ilike '%CAPREM%')
                then coalesce(d.empenhado_liquido, 0)
                else 0
            end
        ) as total_empenhado_patronal,
        sum(
            case
                when d.elemento = '13' and (d.fornecedor_nome ilike '%CAPREM%' or d.natureza_despesa ilike '%RPPS%' or d.natureza_despesa ilike '%CAPREM%' or d.descricao ilike '%CAPREM%')
                then coalesce(d.pago, 0)
                else 0
            end
        ) as total_pago_patronal,
        sum(case when d.elemento = '71' then coalesce(d.pago, 0) else 0 end) as total_amortizacao_divida,
        sum(
            case
                when d.elemento not in ('13', '71', '97') and (d.fornecedor_nome ilike '%CASP%' or d.natureza_despesa ilike '%CASP%' or d.descricao ilike '%CASP%' or d.fornecedor_cpf_cnpj = '07.573.075/0001-00')
                then coalesce(d.empenhado_liquido, 0)
                else 0
            end
        ) as total_casp_plano_saude,
        sum(coalesce(d.empenhado_liquido, 0)) as total_empenhado,
        sum(coalesce(d.liquidado, 0)) as total_liquidado,
        sum(coalesce(d.pago, 0)) as total_pago
    from {{ ref('fct_despesas') }} d
    where
        d.fonte = 'exercicio'
        and (
            d.orgao_codigo = '1061'
            or d.credor_id = '1061'
            or d.fornecedor_nome ilike '%CAPREM%'
            or d.fornecedor_nome ilike '%CASP%'
            or d.fornecedor_cpf_cnpj = '07.573.075/0001-00'
            or d.descricao ilike '%CAPREM%'
            or d.descricao ilike '%CASP%'
        )
        and (d.tipo_empenho is null or d.tipo_empenho != 'AN')
    group by d.portal_slug, d.ano
),

calculos as (
    select
        portal_slug,
        ano,
        total_aporte_exigido::numeric(15, 2) as total_aporte_exigido,
        total_aporte_quitado::numeric(15, 2) as total_aporte_quitado,
        case
            when total_aporte_exigido > 0
            then (total_aporte_quitado / total_aporte_exigido) * 100
            else 100
        end::numeric(15, 4) as taxa_adimplencia_aporte,
        total_empenhado_patronal::numeric(15, 2) as total_empenhado_patronal,
        total_pago_patronal::numeric(15, 2) as total_pago_patronal,
        greatest(0, total_empenhado_patronal - total_pago_patronal)::numeric(15, 2) as rombo_patronal_nao_repassado,
        total_amortizacao_divida::numeric(15, 2) as total_amortizacao_divida,
        total_casp_plano_saude::numeric(15, 2) as total_casp_plano_saude,
        total_empenhado::numeric(15, 2) as total_empenhado,
        total_liquidado::numeric(15, 2) as total_liquidado,
        total_pago::numeric(15, 2) as total_pago
    from despesas_caprem
)

select
    {{ dbt_utils.generate_surrogate_key(['portal_slug', 'ano']) }} as historia_caprem_id,
    portal_slug,
    ano,
    total_aporte_exigido,
    total_aporte_quitado,
    taxa_adimplencia_aporte,
    total_empenhado_patronal,
    total_pago_patronal,
    rombo_patronal_nao_repassado,
    total_amortizacao_divida,
    total_casp_plano_saude,
    total_empenhado,
    total_liquidado,
    total_pago
from calculos
