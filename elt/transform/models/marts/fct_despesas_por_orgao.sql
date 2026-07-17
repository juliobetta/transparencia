select
    empresa,
    ano,
    codigo,
    descricao,
    nullif(replace(empenhado, ',', '.'), '')::numeric as empenhado,
    nullif(replace(liquidado, ',', '.'), '')::numeric as liquidado,
    nullif(replace(pago, ',', '.'), '')::numeric as pago,
    nullif(replace(dotacao_atualizada, ',', '.'), '')::numeric as dotacao_atualizada
from {{ source('porciuncula_prefeitura', 'despesas_por_orgao') }}
