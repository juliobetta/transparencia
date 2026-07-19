-- Fato: receitas consolidadas de todos os portais
-- Prefixos intraorçamentários (17%, 27%) são excluídos na visão multi-entidade pela camada de análise.

with receitas as (
    select
        portal_slug,
        tipo_receita,
        ano,
        empresa_id,
        codigo,
        descricao,
        previsao_atualizada,
        arrecadado_efetivo
    from {{ ref('int_receitas_consolidadas') }}
)

select
    {{ dbt_utils.generate_surrogate_key(['portal_slug', 'ano', 'empresa_id', 'tipo_receita', 'codigo']) }} as receita_id,
    portal_slug,
    ano,
    empresa_id,
    tipo_receita,
    codigo,
    descricao,
    previsao_atualizada,
    arrecadado_efetivo as arrecadado
from receitas
