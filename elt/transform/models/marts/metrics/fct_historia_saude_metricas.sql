{{ config(materialized='table') }}

with dotacao_saude_orgao as (
    select
        'porciuncula_prefeitura' as portal_slug,
        ano,
        sum(coalesce(dotacao_atualizada, 0)) as dotacao_total
    from {{ ref('fct_despesas_por_orgao') }}
    where empresa = '2'
    group by ano
),

linhas_saude as (
    select
        portal_slug,
        ano,
        sum(coalesce(empenhado_liquido, 0)) as total_empenhado,
        sum(coalesce(liquidado, 0)) as total_liquidado,
        sum(coalesce(pago, 0)) as total_pago,
        sum(
            case
                when subfuncao = '303' or subfuncao_nome ilike '%farmac%' or subfuncao_nome ilike '%medicam%'
                then coalesce(empenhado_liquido, 0)
                else 0
            end
        ) as medicamentos_insumos_pago,
        sum(
            case
                when elemento = '91' or elemento ilike '%senten%' or elemento ilike '%judici%'
                then coalesce(empenhado_liquido, 0)
                else 0
            end
        ) as judicializacao_pago
    from {{ ref('fct_despesas') }}
    where fonte = 'exercicio' and (funcao = '10' or empresa_id = '2' or subfuncao = '303')
    group by
        portal_slug,
        ano
),

emendas_saude as (
    select
        portal_slug,
        ano,
        sum(coalesce(nullif(valor_total, 0), coalesce(empenhado, 0))) as emendas_saude_arrecadado
    from {{ ref('fct_emendas') }}
    where empresa_id = '2' or lower(destinacao) ilike '%saud%' or lower(resumo) ilike '%saud%'
    group by portal_slug, ano
),

fornecedores_saude as (
    select
        portal_slug,
        ano,
        coalesce(fornecedor_nome, 'OUTROS') as fornecedor_nome,
        sum(coalesce(empenhado_liquido, 0)) as valor_fornecedor
    from {{ ref('fct_despesas') }}
    where fonte = 'exercicio' and (funcao = '10' or empresa_id = '2' or subfuncao = '303') and coalesce(empenhado_liquido, 0) > 0
    group by portal_slug, ano, coalesce(fornecedor_nome, 'OUTROS')
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
    coalesce(ls.medicamentos_insumos_pago, 0)::numeric(15, 2) as medicamentos_insumos_pago,
    coalesce(ls.judicializacao_pago, 0)::numeric(15, 2) as judicializacao_pago,
    coalesce(es.emendas_saude_arrecadado, 0)::numeric(15, 2) as emendas_saude_arrecadado,
    coalesce(h.hhi_concentracao_fornecedores, 0) as hhi_concentracao_fornecedores
from chaves_base cb
left join dotacao_saude_orgao dso
    on cb.portal_slug = dso.portal_slug
    and cb.ano = dso.ano
left join linhas_saude ls
    on cb.portal_slug = ls.portal_slug
    and cb.ano = ls.ano
left join emendas_saude es
    on cb.portal_slug = es.portal_slug
    and cb.ano = es.ano
left join hhi_calculado h
    on cb.portal_slug = h.portal_slug
    and cb.ano = h.ano
