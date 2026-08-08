{{ config(materialized='table') }}

with despesas_folha as (
    select
        portal_slug,
        ano,
        coalesce(nullif(ltrim(empresa_id, '0'), ''), '0') as empresa_id,
        sum(coalesce(pago, 0)) as total_folha,
        sum(
            case
                when (
                    descricao ilike '%13%'
                    or descricao ilike '%decimo terceiro%'
                    or descricao ilike '%décimo terceiro%'
                )
                and descricao not ilike '%anula%'
                and descricao not ilike '%136%'
                and descricao not ilike '%137%'
                and descricao not ilike '%138%'
                and descricao not ilike '%139%'
                and tipo_empenho != 'AN'
                then coalesce(empenhado_liquido, 0)
                else 0
            end
        ) as empenhado_13,
        sum(
            case
                when (
                    descricao ilike '%13%'
                    or descricao ilike '%decimo terceiro%'
                    or descricao ilike '%décimo terceiro%'
                )
                and descricao not ilike '%anula%'
                and descricao not ilike '%136%'
                and descricao not ilike '%137%'
                and descricao not ilike '%138%'
                and descricao not ilike '%139%'
                and tipo_empenho != 'AN'
                then coalesce(empenhado, 0)
                else 0
            end
        ) as empenhado_bruto_13,
        sum(
            case
                when (
                    descricao ilike '%13%'
                    or descricao ilike '%decimo terceiro%'
                    or descricao ilike '%décimo terceiro%'
                )
                and descricao not ilike '%anula%'
                and descricao not ilike '%136%'
                and descricao not ilike '%137%'
                and descricao not ilike '%138%'
                and descricao not ilike '%139%'
                and tipo_empenho != 'AN'
                then coalesce(liquidado, 0)
                else 0
            end
        ) as liquidado_13,
        sum(
            case
                when (
                    descricao ilike '%13%'
                    or descricao ilike '%decimo terceiro%'
                    or descricao ilike '%décimo terceiro%'
                )
                and descricao not ilike '%anula%'
                and descricao not ilike '%136%'
                and descricao not ilike '%137%'
                and descricao not ilike '%138%'
                and descricao not ilike '%139%'
                and tipo_empenho != 'AN'
                then coalesce(pago, 0)
                else 0
            end
        ) as pago_13
    from {{ ref('fct_despesas') }}
    where elemento in ('01', '03', '11', '96')
    group by portal_slug, ano, coalesce(nullif(ltrim(empresa_id, '0'), ''), '0')
),

despesas_orgao as (
    select
        'porciuncula_prefeitura' as portal_slug,
        ano,
        coalesce(nullif(ltrim(empresa, '0'), ''), '0') as empresa_id,
        sum(coalesce(pago, 0)) as total_pago
    from {{ ref('fct_despesas_por_orgao') }}
    group by ano, coalesce(nullif(ltrim(empresa, '0'), ''), '0')
),

pessoal_stats as (
    select
        portal_slug,
        ano,
        coalesce(nullif(ltrim(empresa_id, '0'), ''), '0') as empresa_id,
        sum(
            case
                when vinculo like '%FG%'
                or vinculo like '%CC%'
                or categoria_funcional = 'Efetivos ocupantes de cargo comissionado'
                then 1
                else 0
            end
        ) as efetivos_confianca,
        sum(
            case
                when categoria_funcional = 'Cargo comissionado extra-quadro'
                or vinculo = 'Comissionado INSS'
                or lower(vinculo) like 'cargo comissionado%'
                then 1
                else 0
            end
        ) as comissionados_externos,
        sum(case when proventos > 0 and proventos < 2500 then 1 else 0 end) as bin_0_25k,
        sum(case when proventos >= 2500 and proventos < 5000 then 1 else 0 end) as bin_25k_5k,
        sum(case when proventos >= 5000 and proventos < 7500 then 1 else 0 end) as bin_5k_75k,
        sum(case when proventos >= 7500 and proventos < 10000 then 1 else 0 end) as bin_75k_10k,
        sum(case when proventos >= 10000 and proventos < 12500 then 1 else 0 end) as bin_10k_125k,
        sum(case when proventos >= 12500 and proventos < 15000 then 1 else 0 end) as bin_125k_15k,
        sum(case when proventos >= 15000 and proventos < 17500 then 1 else 0 end) as bin_15k_175k,
        sum(case when proventos >= 17500 and proventos < 20000 then 1 else 0 end) as bin_175k_20k,
        sum(case when proventos >= 20000 then 1 else 0 end) as bin_acima_20k
    from {{ ref('fct_pessoal') }}
    group by portal_slug, ano, coalesce(nullif(ltrim(empresa_id, '0'), ''), '0')
),

chaves as (
    select portal_slug, ano, empresa_id from despesas_folha
    union
    select portal_slug, ano, empresa_id from despesas_orgao
    union
    select portal_slug, ano, empresa_id from pessoal_stats
)

select
    {{ dbt_utils.generate_surrogate_key(['c.portal_slug', 'c.ano', 'c.empresa_id']) }} as pessoal_folha_metricas_id,
    c.portal_slug,
    c.ano,
    c.empresa_id,
    coalesce(df.total_folha, 0)::numeric(15, 2) as total_folha,
    coalesce(dor.total_pago, 0)::numeric(15, 2) as total_pago,
    coalesce(df.empenhado_13, 0)::numeric(15, 2) as empenhado_13,
    coalesce(df.empenhado_bruto_13, 0)::numeric(15, 2) as empenhado_bruto_13,
    coalesce(df.liquidado_13, 0)::numeric(15, 2) as liquidado_13,
    coalesce(df.pago_13, 0)::numeric(15, 2) as pago_13,
    coalesce(ps.efetivos_confianca, 0)::integer as efetivos_confianca,
    coalesce(ps.comissionados_externos, 0)::integer as comissionados_externos,
    coalesce(ps.bin_0_25k, 0)::integer as bin_0_25k,
    coalesce(ps.bin_25k_5k, 0)::integer as bin_25k_5k,
    coalesce(ps.bin_5k_75k, 0)::integer as bin_5k_75k,
    coalesce(ps.bin_75k_10k, 0)::integer as bin_75k_10k,
    coalesce(ps.bin_10k_125k, 0)::integer as bin_10k_125k,
    coalesce(ps.bin_125k_15k, 0)::integer as bin_125k_15k,
    coalesce(ps.bin_15k_175k, 0)::integer as bin_15k_175k,
    coalesce(ps.bin_175k_20k, 0)::integer as bin_175k_20k,
    coalesce(ps.bin_acima_20k, 0)::integer as bin_acima_20k
from chaves c
left join despesas_folha df
    on c.portal_slug = df.portal_slug
    and c.ano = df.ano
    and c.empresa_id = df.empresa_id
left join despesas_orgao dor
    on c.portal_slug = dor.portal_slug
    and c.ano = dor.ano
    and c.empresa_id = dor.empresa_id
left join pessoal_stats ps
    on c.portal_slug = ps.portal_slug
    and c.ano = ps.ano
    and c.empresa_id = ps.empresa_id
