{{ config(materialized='table') }}

with receitas_base as (
    select
        portal_slug,
        empresa_id,
        ano,
        sum(case when tipo_receita in ('orcamentaria', 'uniao', 'estado') then coalesce(previsao_atualizada, 0) else 0 end) as total_previsto,
        sum(case when tipo_receita in ('orcamentaria', 'uniao', 'estado') then coalesce(arrecadado, 0) else 0 end) as total_arrecadado,
        sum(case when tipo_receita = 'uniao' then coalesce(previsao_atualizada, 0) else 0 end) as transferencias_uniao_previsto,
        sum(case when tipo_receita = 'uniao' then coalesce(arrecadado, 0) else 0 end) as transferencias_uniao_arrecadado,
        sum(case when tipo_receita = 'estado' then coalesce(previsao_atualizada, 0) else 0 end) as transferencias_estado_previsto,
        sum(case when tipo_receita = 'estado' then coalesce(arrecadado, 0) else 0 end) as transferencias_estado_arrecadado,
        sum(
            case
                when codigo ilike '%FPM%' or codigo like '1.7.1.8.01.2%' or codigo like '1718012%' or descricao ilike '%FPM%' or descricao ilike '%FUNDO DE PARTICIPA%' or descricao ilike '%PARTICIPACAO DOS MUNICIPIOS%'
                then coalesce(arrecadado, 0)
                else 0
            end
        ) as fpm_arrecadado,
        sum(
            case
                when codigo ilike '%ICMS%' or codigo like '1.7.2.8.01.1%' or codigo like '1728011%' or descricao ilike '%ICMS%'
                then coalesce(arrecadado, 0)
                else 0
            end
        ) as icms_arrecadado,
        sum(
            case
                when codigo ilike '%ISS%' or codigo ilike '%IPTU%' or codigo like '1.1.1.8.01%' or codigo like '1.1.1.8.02%' or descricao ilike '%IPTU%' or descricao ilike '%ISS%' or descricao ilike '%PROPRIEDADE PREDIA%' or descricao ilike '%SERVICOS DE QUALQUER NATUREZA%'
                then coalesce(arrecadado, 0)
                else 0
            end
        ) as iss_iptu_arrecadado,
        sum(
            case
                when tipo_receita in ('uniao', 'estado', 'orcamentaria') and (descricao ilike '%TRANSFERENCIA ESPECIAL%' or codigo like '1.7.1.5%')
                then coalesce(arrecadado, 0)
                else 0
            end
        ) as emendas_pix_arrecadado,
        sum(
            case
                when tipo_receita in ('uniao', 'estado', 'orcamentaria') and (descricao ilike '%EMENDA%' or descricao ilike '%PARLAMENTAR%') and not (descricao ilike '%TRANSFERENCIA ESPECIAL%' or codigo like '1.7.1.5%')
                then coalesce(arrecadado, 0)
                else 0
            end
        ) as emendas_individuais_arrecadado
    from {{ ref('fct_receitas') }}
    group by portal_slug, empresa_id, ano
),

calculos as (
    select
        portal_slug,
        empresa_id,
        ano,
        greatest(0, total_previsto - transferencias_uniao_previsto - transferencias_estado_previsto)::numeric(15, 2) as receita_propria_previsto,
        greatest(0, total_arrecadado - transferencias_uniao_arrecadado - transferencias_estado_arrecadado)::numeric(15, 2) as receita_propria_arrecadado,
        transferencias_uniao_previsto::numeric(15, 2) as transferencias_uniao_previsto,
        transferencias_uniao_arrecadado::numeric(15, 2) as transferencias_uniao_arrecadado,
        transferencias_estado_previsto::numeric(15, 2) as transferencias_estado_previsto,
        transferencias_estado_arrecadado::numeric(15, 2) as transferencias_estado_arrecadado,
        total_previsto::numeric(15, 2) as total_previsto,
        total_arrecadado::numeric(15, 2) as total_arrecadado,
        fpm_arrecadado::numeric(15, 2) as fpm_arrecadado,
        icms_arrecadado::numeric(15, 2) as icms_arrecadado,
        iss_iptu_arrecadado::numeric(15, 2) as iss_iptu_arrecadado,
        emendas_pix_arrecadado::numeric(15, 2) as emendas_pix_arrecadado,
        emendas_individuais_arrecadado::numeric(15, 2) as emendas_individuais_arrecadado,
        (emendas_pix_arrecadado + emendas_individuais_arrecadado)::numeric(15, 2) as emendas_total_arrecadado
    from receitas_base
)

select
    {{ dbt_utils.generate_surrogate_key(['portal_slug', 'empresa_id', 'ano']) }} as fontes_receita_id,
    portal_slug,
    empresa_id,
    ano,
    receita_propria_previsto,
    receita_propria_arrecadado,
    transferencias_uniao_previsto,
    transferencias_uniao_arrecadado,
    transferencias_estado_previsto,
    transferencias_estado_arrecadado,
    total_previsto,
    total_arrecadado,
    case
        when total_arrecadado > 0
        then (receita_propria_arrecadado / total_arrecadado) * 100
        else
            case
                when total_previsto > 0
                then (receita_propria_previsto / total_previsto) * 100
                else 0
            end
    end::numeric(15, 4) as pct_propria,
    case
        when (
            case
                when total_arrecadado > 0
                then (receita_propria_arrecadado / total_arrecadado) * 100
                else
                    case
                        when total_previsto > 0
                        then (receita_propria_previsto / total_previsto) * 100
                        else 0
                    end
            end
        ) < 10
        then true
        else false
    end as alerta_dependencia,
    fpm_arrecadado,
    icms_arrecadado,
    iss_iptu_arrecadado,
    emendas_pix_arrecadado,
    emendas_individuais_arrecadado,
    emendas_total_arrecadado
from calculos
