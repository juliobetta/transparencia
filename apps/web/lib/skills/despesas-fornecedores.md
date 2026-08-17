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

3. **Subfunções Canônicas STN/MCASP para Itens Específicos**:
   - **Merenda / Alimentação Escolar**: 
     - Subfunção Oficial STN: `subfuncao_codigo = '306'` (Alimentação e Nutrição).
     - Busca textual no histórico: `unaccent(lower(historico))` contendo `'merenda'`, `'alimentacao escolar'` ou `'generos alimenticios'`.
   - **Medicamentos / Insumos de Saúde**:
     - Subfunção Oficial STN: `subfuncao_codigo = '303'` (Suporte Profilático e Terapêutico).
     - Busca textual no histórico: `unaccent(lower(historico))` contendo `'medicamento'` ou `'farmacia'`.

4. **Regras Mandatórias de Lógica Booleana (`AND` vs `OR`) e `unaccent`**:
   - ⚠️ **PROIBIDO USAR `OR` ENTRE TERMO ESPECÍFICO E NOME DE FUNÇÃO BRUTA**: Nunca escreva `WHERE (historico LIKE '%merenda%' OR funcao_nome LIKE '%Educação%')`. Isso inflacionará a consulta trazendo todas as despesas da Educação (folha de pagamento, obras, transporte).
   - ✅ **CORRETO**: Escreva filtros de área como restrição `AND`:
     `WHERE portal_slug = '...' AND ano IN (2025, 2026) AND (unaccent(lower(historico)) LIKE '%merenda%' OR unaccent(lower(historico)) LIKE '%alimentacao%escolar%' OR subfuncao_codigo = '306')`
   - **Acentuação**: Sempre use `unaccent(lower(coluna))` com padrões sem acento (ex: `'alimentacao'`, não `'alimentação'`).
