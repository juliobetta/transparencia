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
    group by d.portal_slug, d.ano
),

pessoal_caprem as (
    select
        portal_slug,
        ano,
        sum(case when categoria_funcional ilike '%efetiv%' and categoria_funcional not ilike '%cedido%' then 1 else 0 end) as servidores_efetivos,
        sum(case when categoria_funcional ilike '%comissionad%' or categoria_funcional ilike '%contrata%' or categoria_funcional ilike '%excepcional%' then 1 else 0 end) as servidores_temporarios
    from {{ ref('fct_pessoal') }}
    group by portal_slug, ano
),

calculos as (
    select
        d.portal_slug,
        d.ano,
        d.total_aporte_exigido::numeric(15, 2) as total_aporte_exigido,
        d.total_aporte_quitado::numeric(15, 2) as total_aporte_quitado,
        case
            when d.total_aporte_exigido > 0
            then (d.total_aporte_quitado / d.total_aporte_exigido) * 100
            else 100
        end::numeric(15, 4) as taxa_adimplencia_aporte,
        d.total_empenhado_patronal::numeric(15, 2) as total_empenhado_patronal,
        d.total_pago_patronal::numeric(15, 2) as total_pago_patronal,
        greatest(0, d.total_empenhado_patronal - d.total_pago_patronal)::numeric(15, 2) as rombo_patronal_nao_repassado,
        d.total_amortizacao_divida::numeric(15, 2) as total_amortizacao_divida,
        d.total_casp_plano_saude::numeric(15, 2) as total_casp_plano_saude,
        d.total_empenhado::numeric(15, 2) as total_empenhado,
        d.total_liquidado::numeric(15, 2) as total_liquidado,
        d.total_pago::numeric(15, 2) as total_pago,
        coalesce(p.servidores_efetivos, 0)::integer as servidores_efetivos,
        coalesce(p.servidores_temporarios, 0)::integer as servidores_temporarios
    from despesas_caprem d
    left join pessoal_caprem p
        on d.portal_slug = p.portal_slug
        and d.ano = p.ano
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
    total_pago,
    servidores_efetivos,
    servidores_temporarios
from calculos
