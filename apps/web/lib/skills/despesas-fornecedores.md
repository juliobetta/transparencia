# Skill: Análise de Despesas, Credores e Tipos de Empenho

## Tipos de Empenho (`tpem`) e Empenho Líquido
1. **Natureza dos Tipos de Empenho (`tpem`)**:
   - `OR` (Ordinário): Despesa com valor fixo e conhecido previamente, paga de uma vez.
   - `ES` (Estimativo): Despesa de valor variável/incerto (clássico para Folha de Pagamento e concessionárias).
   - `GL` (Global): Despesa contratual parcelada ao longo do exercício (locações, contratos continuados).
   - `AN` (Anulação): Estorno ou cancelamento oficial de saldo reservado.

2. **Cálculo do Empenho Líquido (Ajustado)**:
   $$\text{Empenho Líquido} = \text{Empenho Bruto} + \text{Anulações (Valores Negativos)}$$
   - Valores negativos representam anulações/estornos contábeis oficiais e jamais devem ser ignorados.

3. **Análise de Concentração de Credores (HHI)**:
   - `participacao_pct`: Percentual do credor sobre o total pago pelo município.
   - HHI > 0.25 indica alta concentração de gastos em poucos fornecedores.

4. **Regras SQL**:
   - Para busca de credores, utilizar `ILIKE '%termo%'`.
   - Utilize `unaccent` na coluna `fornecedor_nome` ou outra similar para evitar problemas com acentuação. ex: `WHERE unaccent(fornecedor_nome) ILIKE unaccent('%termo%')`.
   - Agrupar por `fornecedor_nome` ou `orgao_codigo` aplicando obrigatoriamente `portal_slug` e `ano`.
