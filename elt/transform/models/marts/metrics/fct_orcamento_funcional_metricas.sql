

with linhas_orcamentarias as (
    select
        portal_slug,
        empresa_id,
        ano,
        coalesce(funcao_nome, 'Sem função') as funcao_nome,
        coalesce(subfuncao_nome, 'Sem subfunção') as subfuncao_nome,
        orgao_codigo,
        unidade_codigo,
        funcao,
        subfuncao,
        programa,
        proj_atividade,
        natureza_despesa,
        max(coalesce(dotacao_atualizada, 0)) as dotacao_linha,
        sum(coalesce(empenhado_liquido, 0)) as empenhado_linha,
        sum(coalesce(liquidado, 0)) as liquidado_linha,
        sum(coalesce(pago, 0)) as pago_linha
    from {{ ref('fct_despesas') }}
    where fonte = 'exercicio' and ano is not null
    group by
        portal_slug,
        empresa_id,
        ano,
        coalesce(funcao_nome, 'Sem função'),
        coalesce(subfuncao_nome, 'Sem subfunção'),
        orgao_codigo,
        unidade_codigo,
        funcao,
        subfuncao,
        programa,
        proj_atividade,
        natureza_despesa
),

despesas_funcionais as (
    select
        portal_slug,
        empresa_id,
        ano,
        funcao_nome,
        subfuncao_nome,
        sum(dotacao_linha) as dotacao_atualizada,
        sum(empenhado_linha) as empenhado,
        sum(liquidado_linha) as liquidado,
        sum(pago_linha) as pago
    from linhas_orcamentarias
    group by
        portal_slug,
        empresa_id,
        ano,
        funcao_nome,
        subfuncao_nome
)

select
    {{ dbt_utils.generate_surrogate_key(['portal_slug', 'empresa_id', 'ano', 'funcao_nome', 'subfuncao_nome']) }} as orcamento_funcional_id,
    portal_slug,
    empresa_id,
    ano,
    funcao_nome,
    subfuncao_nome,
    dotacao_atualizada::numeric(15, 2) as dotacao_atualizada,
    empenhado::numeric(15, 2) as empenhado,
    liquidado::numeric(15, 2) as liquidado,
    pago::numeric(15, 2) as pago
from despesas_funcionais
