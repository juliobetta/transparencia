{{ config(
    materialized='table',
    pre_hook="create extension if not exists unaccent;"
) }}

with orgaos_saude as (
    select portal_slug, empresa_id
    from {{ ref('dim_orgao') }}
    where lower(unaccent(orgao_nome)) ilike '%saude%'
),

dotacao_saude_orgao as (
    select
        'porciuncula_prefeitura' as portal_slug,
        d.ano,
        sum(coalesce(d.dotacao_atualizada, 0)) as dotacao_total
    from {{ ref('fct_despesas_por_orgao') }} d
    join orgaos_saude o
        on d.empresa = o.empresa_id
    group by d.ano
),

linhas_saude as (
    select
        d.portal_slug,
        d.ano,
        sum(coalesce(d.empenhado_liquido, 0)) as total_empenhado,
        sum(coalesce(d.liquidado, 0)) as total_liquidado,
        sum(coalesce(d.pago, 0)) as total_pago,
        sum(
            case
                when d.subfuncao = '303' or d.subfuncao_nome ilike '%farmac%' or d.subfuncao_nome ilike '%medicam%'
                then coalesce(d.empenhado_liquido, 0)
                else 0
            end
        ) as medicamentos_insumos_empenhado,
        sum(
            case
                when d.subfuncao = '303' or d.subfuncao_nome ilike '%farmac%' or d.subfuncao_nome ilike '%medicam%'
                then coalesce(d.pago, 0)
                else 0
            end
        ) as medicamentos_insumos_pago,
        sum(
            case
                when d.elemento = '91' or d.elemento ilike '%senten%' or d.elemento ilike '%judici%'
                then coalesce(d.empenhado_liquido, 0)
                else 0
            end
        ) as judicializacao_empenhado,
        sum(
            case
                when d.elemento = '91' or d.elemento ilike '%senten%' or d.elemento ilike '%judici%'
                then coalesce(d.pago, 0)
                else 0
            end
        ) as judicializacao_pago
    from {{ ref('fct_despesas') }} d
    left join orgaos_saude o
        on d.portal_slug = o.portal_slug
        and d.empresa_id = o.empresa_id
    where d.fonte = 'exercicio' and (d.funcao = '10' or o.empresa_id is not null or d.subfuncao = '303')
    group by
        d.portal_slug,
        d.ano
),

receitas_saude as (
    select
        r.portal_slug,
        r.ano,
        sum(
            case
                when r.tipo_receita = 'uniao' and r.codigo in ('1713.00.0.0.00.00', '2411.00.0.0.00.00')
                then coalesce(r.arrecadado, 0)
                else 0
            end
        ) as receita_uniao,
        sum(
            case
                when r.tipo_receita = 'estado' and r.codigo in ('1720.00.0.0.00.00', '1723.50.0.1.00.00', '2420.00.0.0.00.00')
                then coalesce(r.arrecadado, 0)
                else 0
            end
        ) as receita_estado
    from {{ ref('fct_receitas') }} r
    join orgaos_saude o
        on r.portal_slug = o.portal_slug
        and r.empresa_id = o.empresa_id
    group by r.portal_slug, r.ano
),

emendas_saude as (
    select
        e.portal_slug,
        e.ano,
        sum(coalesce(nullif(e.valor_total, 0), coalesce(e.empenhado, 0))) as emendas_saude_arrecadado
    from {{ ref('fct_emendas') }} e
    left join orgaos_saude o
        on e.portal_slug = o.portal_slug
        and e.empresa_id = o.empresa_id
    where o.empresa_id is not null or lower(unaccent(e.destinacao)) ilike '%saud%' or lower(unaccent(e.resumo)) ilike '%saud%'
    group by e.portal_slug, e.ano
),

fornecedores_saude as (
    select
        d.portal_slug,
        d.ano,
        coalesce(d.fornecedor_nome, 'OUTROS') as fornecedor_nome,
        sum(coalesce(d.empenhado_liquido, 0)) as valor_fornecedor
    from {{ ref('fct_despesas') }} d
    left join orgaos_saude o
        on d.portal_slug = o.portal_slug
        and d.empresa_id = o.empresa_id
    where d.fonte = 'exercicio' and (d.funcao = '10' or o.empresa_id is not null or d.subfuncao = '303') and coalesce(d.empenhado_liquido, 0) > 0
    group by d.portal_slug, d.ano, coalesce(d.fornecedor_nome, 'OUTROS')
),

totais_fornecedores as (
    select
        portal_slug,
        ano,
        sum(valor_fornecedor) as total_fornecedores
    from fornecedores_saude
    group by portal_slug, ano
),

hhi_calculado as (
    select
        f.portal_slug,
        f.ano,
        round(sum(power(f.valor_fornecedor / nullif(t.total_fornecedores, 0), 2)) * 10000)::integer as hhi_concentracao_fornecedores
    from fornecedores_saude f
    join totais_fornecedores t
        on f.portal_slug = t.portal_slug
        and f.ano = t.ano
    group by f.portal_slug, f.ano
),

chaves_base as (
    select portal_slug, ano from dotacao_saude_orgao
    union
    select portal_slug, ano from linhas_saude
    union
    select portal_slug, ano from emendas_saude
)

select
    {{ dbt_utils.generate_surrogate_key(['cb.portal_slug', 'cb.ano']) }} as historia_saude_id,
    cb.portal_slug,
    cb.ano,
    coalesce(dso.dotacao_total, ls.total_empenhado, 0)::numeric(15, 2) as dotacao_total,
    coalesce(ls.total_empenhado, 0)::numeric(15, 2) as total_empenhado,
    coalesce(ls.total_liquidado, 0)::numeric(15, 2) as total_liquidado,
    coalesce(ls.total_pago, 0)::numeric(15, 2) as total_pago,
    coalesce(ls.medicamentos_insumos_empenhado, 0)::numeric(15, 2) as medicamentos_insumos_empenhado,
    coalesce(ls.medicamentos_insumos_pago, 0)::numeric(15, 2) as medicamentos_insumos_pago,
    coalesce(ls.judicializacao_empenhado, 0)::numeric(15, 2) as judicializacao_empenhado,
    coalesce(ls.judicializacao_pago, 0)::numeric(15, 2) as judicializacao_pago,
    coalesce(es.emendas_saude_arrecadado, 0)::numeric(15, 2) as emendas_saude_arrecadado,
    coalesce(h.hhi_concentracao_fornecedores, 0) as hhi_concentracao_fornecedores,
    coalesce(rs.receita_uniao, 0)::numeric(15, 2) as receita_uniao_saude,
    coalesce(rs.receita_estado, 0)::numeric(15, 2) as receita_estado_saude,
    greatest(0, coalesce(ls.total_empenhado, 0) - coalesce(rs.receita_uniao, 0) - coalesce(rs.receita_estado, 0))::numeric(15, 2) as repasses_prefeitura_saude,
    case
        when coalesce(ls.total_empenhado, 0) > 0
        then round((coalesce(rs.receita_uniao, 0) / greatest(coalesce(ls.total_empenhado, 0), coalesce(rs.receita_uniao, 0) + coalesce(rs.receita_estado, 0))) * 100)::integer
        else 0
    end as uniao_sus_pct,
    case
        when coalesce(ls.total_empenhado, 0) > 0
        then round((coalesce(rs.receita_estado, 0) / greatest(coalesce(ls.total_empenhado, 0), coalesce(rs.receita_uniao, 0) + coalesce(rs.receita_estado, 0))) * 100)::integer
        else 0
    end as estado_pct,
    case
        when coalesce(ls.total_empenhado, 0) > 0
        then greatest(0, 100 - round((coalesce(rs.receita_uniao, 0) / greatest(coalesce(ls.total_empenhado, 0), coalesce(rs.receita_uniao, 0) + coalesce(rs.receita_estado, 0))) * 100)::integer - round((coalesce(rs.receita_estado, 0) / greatest(coalesce(ls.total_empenhado, 0), coalesce(rs.receita_uniao, 0) + coalesce(rs.receita_estado, 0))) * 100)::integer)::integer
        else 0
    end as propria_pct
from chaves_base cb
left join dotacao_saude_orgao dso
    on cb.portal_slug = dso.portal_slug
    and cb.ano = dso.ano
left join linhas_saude ls
    on cb.portal_slug = ls.portal_slug
    and cb.ano = ls.ano
left join receitas_saude rs
    on cb.portal_slug = rs.portal_slug
    and cb.ano = rs.ano
left join emendas_saude es
    on cb.portal_slug = es.portal_slug
    and cb.ano = es.ano
left join hhi_calculado h
    on cb.portal_slug = h.portal_slug
    and cb.ano = h.ano
