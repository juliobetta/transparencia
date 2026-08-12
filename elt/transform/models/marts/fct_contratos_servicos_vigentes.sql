{{ config(
    materialized='table'
) }}

with contratos_base as (
    select
        c.portal_slug,
        c.empresa_id,
        c.ano,
        c.contrato_numero,
        c.fornecedor_nome,
        c.fornecedor_cpf_cnpj as fornecedor_cnpj,
        regexp_replace(c.fornecedor_cpf_cnpj, '[^\d]', '', 'g') as cnpj_clean,
        coalesce(c.objeto_completo, c.objeto, 'contrato_prestacao_servicos') as objeto_descricao,
        c.data_inicio,
        c.vencimento_atual,
        coalesce(c.valor_contrato, 0) as valor_contrato_inicial,
        coalesce(c.valor_aditado, 0) as valor_aditado,
        (coalesce(c.valor_contrato, 0) + coalesce(c.valor_aditado, 0)) as valor_contrato_total,
        coalesce(nullif(c.empenhado, 0), (coalesce(c.valor_contrato, 0) + coalesce(c.valor_aditado, 0)), 0) as empenhado_contrato
    from {{ ref('fct_contratos') }} c
    where c.fornecedor_cpf_cnpj is not null
      and (c.data_inicio is null or extract(year from c.data_inicio) <= c.ano)
      and (c.vencimento_atual is null or extract(year from c.vencimento_atual) >= c.ano)
),

totais_fornecedor as (
    select
        portal_slug,
        empresa_id,
        ano,
        cnpj_clean,
        sum(empenhado_contrato) as sum_empenhado_contrato
    from contratos_base
    group by portal_slug, empresa_id, ano, cnpj_clean
),

despesas_fornecedor as (
    select
        portal_slug,
        empresa_id,
        ano,
        regexp_replace(fornecedor_cpf_cnpj, '[^\d]', '', 'g') as cnpj_clean,
        sum(coalesce(liquidado, 0)) as total_liquidado,
        sum(coalesce(pago, 0)) as total_pago
    from {{ ref('fct_despesas') }}
    where fornecedor_cpf_cnpj is not null
    group by portal_slug, empresa_id, ano, regexp_replace(fornecedor_cpf_cnpj, '[^\d]', '', 'g')
),

calculado as (
    select
        cb.portal_slug,
        cb.empresa_id,
        cb.ano,
        cb.contrato_numero,
        cb.fornecedor_nome,
        cb.fornecedor_cnpj,
        cb.objeto_descricao,
        cb.data_inicio,
        cb.vencimento_atual,
        cb.valor_aditado,
        cb.empenhado_contrato,
        round(coalesce(df.total_liquidado, 0) * (cb.empenhado_contrato / nullif(tf.sum_empenhado_contrato, 0)), 2) as liquidado_calc,
        round(coalesce(df.total_pago, 0) * (cb.empenhado_contrato / nullif(tf.sum_empenhado_contrato, 0)), 2) as pago_calc
    from contratos_base cb
    join totais_fornecedor tf
        on cb.portal_slug = tf.portal_slug
       and cb.empresa_id = tf.empresa_id
       and cb.ano = tf.ano
       and cb.cnpj_clean = tf.cnpj_clean
    left join despesas_fornecedor df
        on cb.portal_slug = df.portal_slug
       and cb.empresa_id = df.empresa_id
       and cb.ano = df.ano
       and cb.cnpj_clean = df.cnpj_clean
)

select
    {{ dbt_utils.generate_surrogate_key(['portal_slug', 'empresa_id', 'ano', 'coalesce(contrato_numero, \'\')', 'regexp_replace(fornecedor_cnpj, \'[^\d]\', \'\', \'g\')']) }} as contrato_servico_id,
    portal_slug,
    empresa_id,
    ano,
    contrato_numero,
    fornecedor_nome,
    fornecedor_cnpj,
    objeto_descricao,
    data_inicio,
    vencimento_atual,
    valor_aditado::numeric(15, 2) as valor_aditado,
    greatest(empenhado_contrato, coalesce(liquidado_calc, 0))::numeric(15, 2) as total_empenhado,
    coalesce(liquidado_calc, 0)::numeric(15, 2) as total_liquidado,
    least(coalesce(pago_calc, 0), coalesce(liquidado_calc, 0))::numeric(15, 2) as total_pago
from calculado
order by ano desc, total_pago asc, (greatest(empenhado_contrato, coalesce(liquidado_calc, 0)) - least(coalesce(pago_calc, 0), coalesce(liquidado_calc, 0))) desc
