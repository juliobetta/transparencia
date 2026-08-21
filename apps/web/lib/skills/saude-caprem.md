# Skill: Saúde Pública e Previdência Municipal (CAPREM)

## Diretrizes Contábeis
1. **Saúde Pública**:
   - Aplicação Mínima Constitucional em Ações e Serviços Públicos de Saúde (ASPS) conforme LC 141/2012 (mínimo de 15% das receitas de impostos).
   - O mart `fct_historia_saude_metricas` consolida totais liquidados, pagos e percentual de aplicação.
   - **Filtro de Área por Entidade/Órgão (`empresa_id` e `dim_orgao`)**: Em perguntas sobre emendas, despesas, licitações ou contratos direcionados à Saúde (ex: "quanto de emendas foram para a saúde?"), o filtro SQL deve OBRIGATORIAMENTE incluir a Entidade Fiscal `empresa_id` (via `dim_orgao`) combinando (`OR`) com buscas textuais (`destinacao` ou `resumo`), pois várias emendas e despesas de saúde têm descrições sem a palavra 'saúde' (ex: "AQUISIÇÃO DE EQUIPAMENTO", "CUSTEIO MAC"). Exemplo: `WHERE portal_slug = '{portalSlug}' AND ano = {ano} AND (empresa_id IN (SELECT empresa_id FROM dim_orgao WHERE portal_slug = '{portalSlug}' AND unaccent(lower(orgao_nome)) LIKE '%saude%') OR unaccent(lower(COALESCE(destinacao,''))) LIKE '%saude%' OR unaccent(lower(COALESCE(resumo,''))) LIKE '%saude%')`.
2. **Previdência (CAPREM)**:
   - **Acumulado do Exercício**: Todas as métricas monetárias representam o acumulado acumulado no exercício fiscal (ano) até o momento, NUNCA parcelas mensais isoladas.
   - **Distinção de Escopo**:
     - **Total Consolidado do Domínio CAPREM/CASP** (`total_empenhado`, `total_liquidado`, `total_pago`): Soma de todas as despesas do RPPS e CASP (Aporte Atuarial Deficitário + Amortização de Dívida + Plano de Saúde CASP + Obrigação Patronal).
     - **Contribuição Patronal Específica** (`total_empenhado_patronal`, `total_liquidado_patronal`, `total_pago_patronal`): Refere-se estritamente às obrigações patronais da folha (Elemento 13).
     - **Rombo Patronal Não Repassado** (`rombo_patronal_nao_repassado`): Saldo acumulado no exercício da diferença entre a Obrigação Patronal Liquidada e a Paga (`total_liquidado_patronal - total_pago_patronal`).

