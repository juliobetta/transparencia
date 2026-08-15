

with restos as (
    select
        portal_slug,
        empresa_id,
        ano,
        trim(regexp_replace(coalesce(descricao, 'Sem identificação'), '^\d{2}\.\d{3}\.\d{3}\s+', '')) as fornecedor_nome,
        coalesce(empenhado, 0) - coalesce(pago, 0) as valor_pendente
    from {{ ref('fct_despesas') }}
    where fonte = 'restos_a_pagar'
      and ano is not null
      and ano >= {{ var('administracao_min_valid_year', 2000) }}
      and ano <= extract(year from current_date)
),
with_ano_atual as (
    select
        portal_slug,
        empresa_id,
        ano,
        fornecedor_nome,
        valor_pendente,
        max(ano) over (
            partition by portal_slug, empresa_id
        ) as ano_atual
    from restos
),
indices_mandato as (
    select
        portal_slug,
        empresa_id,
        ano,
        fornecedor_nome,
        valor_pendente,
        ano_atual,
        floor((coalesce(ano, 0) - {{ var('administracao_reference_year', 2025) }}) / 4) as indice_mandato_ano,
        floor((coalesce(ano_atual, coalesce(ano, 0)) - {{ var('administracao_reference_year', 2025) }}) / 4) as indice_mandato_atual
    from with_ano_atual
),
classified as (
    select
        portal_slug,
        empresa_id,
        ano,
        case
            when indice_mandato_ano = indice_mandato_atual then 'Adm. Atual'
            else 'Adm. Anterior'
        end as administracao,
        fornecedor_nome,
        valor_pendente
    from indices_mandato
),
aggregated as (
    select
        portal_slug,
        empresa_id,
        ano,
        administracao,
        fornecedor_nome,
        sum(coalesce(valor_pendente, 0)) as valor_pendente
    from classified
    group by
        portal_slug,
        empresa_id,
        ano,
        administracao,
        fornecedor_nome
)

select
    {{ dbt_utils.generate_surrogate_key(['portal_slug', 'empresa_id', 'ano', 'administracao', 'fornecedor_nome']) }} as posicao_fiscal_detalhes_id,
    portal_slug,
    empresa_id,
    ano,
    administracao,
    coalesce(valor_pendente, 0) as valor_pendente,
    fornecedor_nome
from aggregated
where coalesce(valor_pendente, 0) > 0
