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

4. **Segregação de Restos a Pagar (RAP) e Variação entre Exercícios**:
   - `restos_pendentes_adm_anterior`: Dívidas de gestões políticas anteriores (governos passados). NUNCA utilizar esta coluna como substituto do ano anterior ($N-1$).
   - `restos_pendentes_adm_atual`: Dívidas geradas dentro do mandato atual pendentes de quitação.
   - **Variação de RAP entre Exercícios**: Para responder sobre variações em relação ao ano anterior, consulte obrigatoriamente a linha do ano $N-1$ e a linha do ano $N$ (ex: `WHERE ano IN (2025, 2026)`).

5. **Segregação de Passivos Financeiros vs. Contratos Futuros (Proibição de Dupla Contagem)**:
   - **NÃO somar Saldo de Contratos com Restos a Pagar**: Saldo futuro a empenhar de contratos representa previsão de execução orçamentária futura, NÃO um passivo financeiro exigível.
   - **Risco de Dupla Contagem**: Parcelas executadas dos contratos já são inscritas em Restos a Pagar. Somá-los duplica obrigações.
   - **Passivo Financeiro Exigível**: Refere-se estritamente a Restos a Pagar (Processados e Não Processados) e despesas liquidadas não pagas.

6. **Regras SQL para PostgreSQL**:
   - Toda consulta no PostgreSQL deve incluir a cláusula `WHERE portal_slug = '{portalSlug}' AND ano = {ano}`.
   - Utilize a função `unaccent(lower(coluna))` para buscas textuais case e acento-insensitive.
