select
    empresa,
    ano::int as ano,
    codigo,
    descricao,
    insmf as fornecedor_cpf_cnpj,
    cepci as fornecedor_cidade,
    nullif(replace(empenhado, ',', '.'), '')::numeric as empenhado,
    nullif(replace(liquidado, ',', '.'), '')::numeric as liquidado,
    nullif(replace(pago, ',', '.'), '')::numeric as pago
from {{ source('porciuncula_prefeitura', 'despesas_por_fornecedor') }}
