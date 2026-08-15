# Skill: Posição Fiscal, Caixa e Balanço Orçamentário (STN/MCASP)

## Axiomas e Regras da Despesa Pública
1. **Axioma Linear da Execução**:
   - Cronologia obrigatória: $Pago \le Liquidado \le Empenhado$.
   - **Proibição de Dupla Contagem**: É terminantemente proibido somar valores de estágios diferentes (Empenhado + Liquidado + Pago) para computar um indicador único de "Gasto".
   - Utilizar termos inequívocos: "Total Empenhado", "Serviços Liquidados" e "Efetivamente Pago".

2. **Fórmulas e Saldos Fiscais**:
   - `total_arrecadado`: Arrecadação de receitas orçamentárias (nó raiz da hierarquia, excluindo transferências intraorçamentárias de prefixos 17% e 27% em visões multi-entidade).
   - `despesas_pagas`: Pagamentos efetivamente quitados.
   - `saldo_estimado`: Calculado estritamente como `total_arrecadado - despesas_pagas`.
   - `Saldo_Disponível` Orçamentário = `Dotação_Atualizada - Valor_Empenhado`.

3. **Paradoxo do Caixa vs. Orçamento**:
   - Um saldo de dotação zerado indica apenas impedimento legal para novos empenhos naquela ação pública específica; jamais inferir falta de recursos bancários em caixa unicamente por essa métrica.

4. **Segregação de Restos a Pagar (RAP)**:
   - `restos_pendentes_adm_anterior`: Dívidas de exercícios/gestões passadas pendentes.
   - `restos_pendentes_adm_atual`: Dívidas geradas no exercício vigente pendentes de quitação.

5. **Regras SQL para DuckDB**:
   - Toda consulta no DuckDB deve incluir a cláusula `WHERE portal_slug = '{portalSlug}' AND ano = {ano}`.
   - Proteger somatórios com `CAST(SUM(...) AS DOUBLE)` para evitar estouro de 128-bit (`HugeInt`).
