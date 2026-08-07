{{
    config(
        materialized='table',
        pre_hook=[
            "create extension if not exists unaccent;"
        ]
    )
}}

with receitas_root as (
    select
        t.portal_slug,
        t.empresa_id,
        t.ano,
        t.previsao_atualizada,
        t.arrecadado
    from {{ ref('fct_receitas') }} t
    where t.tipo_receita = 'orcamentaria'
      and not exists (
        select 1 from {{ ref('fct_receitas') }} t2
        where t2.tipo_receita = t.tipo_receita
          and t2.ano = t.ano
          and t2.empresa_id = t.empresa_id
          and t2.codigo != t.codigo
          and t.codigo like rtrim(t2.codigo, '0.') || '%'
          and length(rtrim(t2.codigo, '0.')) < length(rtrim(t.codigo, '0.'))
      )
),

totais_orcamentarios as (
    select
        portal_slug,
        empresa_id,
        ano,
        sum(coalesce(previsao_atualizada, 0)) as total_previsto,
        sum(coalesce(arrecadado, 0)) as total_arrecadado
    from receitas_root
    group by portal_slug, empresa_id, ano
),

receitas_breakdown_root as (
    select
        t.portal_slug,
        t.empresa_id,
        t.ano,
        t.tipo_receita,
        t.codigo,
        t.descricao,
        t.previsao_atualizada,
        t.arrecadado
    from {{ ref('fct_receitas') }} t
    where not exists (
        select 1 from {{ ref('fct_receitas') }} t2
        where t2.tipo_receita = t.tipo_receita
          and t2.ano = t.ano
          and t2.empresa_id = t.empresa_id
          and t2.codigo != t.codigo
          and t.codigo like rtrim(t2.codigo, '0.') || '%'
          and length(rtrim(t2.codigo, '0.')) < length(rtrim(t.codigo, '0.'))
    )
),

receitas_breakdown as (
    select
        portal_slug,
        empresa_id,
        ano,
        sum(case when tipo_receita = 'uniao' then coalesce(previsao_atualizada, 0) else 0 end) as transferencias_uniao_previsto,
        sum(case when tipo_receita = 'uniao' then coalesce(arrecadado, 0) else 0 end) as transferencias_uniao_arrecadado,
        sum(case when tipo_receita = 'estado' then coalesce(previsao_atualizada, 0) else 0 end) as transferencias_estado_previsto,
        sum(case when tipo_receita = 'estado' then coalesce(arrecadado, 0) else 0 end) as transferencias_estado_arrecadado,
        sum(
            case
                when tipo_receita in ('uniao', 'estado', 'orcamentaria') and ({{ target.schema }}.unaccent(descricao) ilike '%TRANSFERENCIA ESPECIAL%' or codigo like '1.7.1.5%')
                then coalesce(arrecadado, 0)
                else 0
            end
        ) as emendas_pix_arrecadado,
        sum(
            case
                when tipo_receita in ('uniao', 'estado', 'orcamentaria') and (descricao ilike '%EMENDA%' or descricao ilike '%PARLAMENTAR%') and not ({{ target.schema }}.unaccent(descricao) ilike '%TRANSFERENCIA ESPECIAL%' or codigo like '1.7.1.5%')
                then coalesce(arrecadado, 0)
                else 0
            end
        ) as emendas_individuais_arrecadado
    from receitas_breakdown_root
    group by portal_slug, empresa_id, ano
),

carros_chefe as (
    select
        portal_slug,
        empresa_id,
        ano,
        sum(
            case
                when codigo ilike '%FPM%' or codigo like '1.7.1.8.01.2%' or codigo like '1718012%' or descricao ilike '%FPM%' or descricao ilike '%FUNDO DE PARTICIPA%' or {{ target.schema }}.unaccent(descricao) ilike '%PARTICIPACAO DOS MUNICIPIOS%'
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
                when codigo ilike '%ISS%' or codigo ilike '%IPTU%' or codigo like '1.1.1.8.01%' or codigo like '1.1.1.8.02%' or descricao ilike '%IPTU%' or descricao ilike '%ISS%' or descricao ilike '%PROPRIEDADE PREDIA%' or {{ target.schema }}.unaccent(descricao) ilike '%SERVICOS DE QUALQUER NATUREZA%'
                then coalesce(arrecadado, 0)
                else 0
            end
        ) as iss_iptu_arrecadado
    from {{ ref('fct_receitas') }}
    group by portal_slug, empresa_id, ano
),

emendas_fct as (
    select
        portal_slug,
        empresa_id,
        ano,
        sum(
            case
                when lower(tipo_emenda) like '%especial%' or lower(tipo_emenda) like '%pix%'
                then coalesce(valor_total, empenhado, 0)
                else 0
            end
        ) as emendas_pix_fct,
        sum(
            case
                when not (lower(tipo_emenda) like '%especial%' or lower(tipo_emenda) like '%pix%')
                then coalesce(valor_total, empenhado, 0)
                else 0
            end
        ) as emendas_individuais_fct
    from {{ ref('fct_emendas') }}
    group by portal_slug, empresa_id, ano
),

receitas_base as (
    select
        t.portal_slug,
        t.empresa_id,
        t.ano,
        t.total_previsto,
        t.total_arrecadado,
        coalesce(b.transferencias_uniao_previsto, 0) as transferencias_uniao_previsto,
        coalesce(b.transferencias_uniao_arrecadado, 0) as transferencias_uniao_arrecadado,
        coalesce(b.transferencias_estado_previsto, 0) as transferencias_estado_previsto,
        coalesce(b.transferencias_estado_arrecadado, 0) as transferencias_estado_arrecadado,
        coalesce(c.fpm_arrecadado, 0) as fpm_arrecadado,
        coalesce(c.icms_arrecadado, 0) as icms_arrecadado,
        coalesce(c.iss_iptu_arrecadado, 0) as iss_iptu_arrecadado,
        case
            when ef.portal_slug is not null and (ef.emendas_pix_fct > 0 or ef.emendas_individuais_fct > 0)
            then ef.emendas_pix_fct
            else coalesce(b.emendas_pix_arrecadado, 0)
        end as emendas_pix_arrecadado,
        case
            when ef.portal_slug is not null and (ef.emendas_pix_fct > 0 or ef.emendas_individuais_fct > 0)
            then ef.emendas_individuais_fct
            else coalesce(b.emendas_individuais_arrecadado, 0)
        end as emendas_individuais_arrecadado
    from totais_orcamentarios t
    left join receitas_breakdown b
        on t.portal_slug = b.portal_slug
        and t.empresa_id = b.empresa_id
        and t.ano = b.ano
    left join carros_chefe c
        on t.portal_slug = c.portal_slug
        and t.empresa_id = c.empresa_id
        and t.ano = c.ano
    left join emendas_fct ef
        on t.portal_slug = ef.portal_slug
        and t.empresa_id = ef.empresa_id
        and t.ano = ef.ano
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
