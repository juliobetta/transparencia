# Design: Melhoria da Visualização do Ciclo da Despesa

## 1. Objetivo
Transformar a página `orcamento.py` em uma ferramenta didática e precisa de acompanhamento do ciclo orçamentário, diferenciando claramente: **Dotação Atualizada**, **Empenhado**, **Liquidado** e **Pago**.

## 2. Componentes e Alterações
- **Camada de Análise (`analysis/budget_execution.py`):**
    - Verificar se a função `summarize` já agrega os quatro valores. Caso contrário, atualizar para incluir `total_liquidado` e `total_pago`.
- **Camada de Interface (`dashboard/pages/orcamento.py`):**
    - **Header:** Expandir de 3 para 4 métricas, apresentando os quatro estágios do ciclo.
    - **Gráfico:** Substituir o gráfico de barras simples por um gráfico de funil (`px.funnel`), que demonstra visualmente a redução do valor disponível conforme a execução avança.
    - **Tooltips:** Utilizar o módulo `glossary` para explicar cada termo, garantindo a conformidade com a skill `BR-MUNICIPAL-BUDGET-ENGINEER`.

## 3. UX de Controle Social
- Manter as legendas informativas (`st.caption`) reforçando que o Funil demonstra a execução técnica, não necessariamente a disponibilidade imediata de caixa (exceto no estágio de Pagamento).
