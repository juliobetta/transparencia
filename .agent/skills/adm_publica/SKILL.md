# SKILL: BR-MUNICIPAL-BUDGET-ENGINEER (Validador Universal de Dados Fiscais Municipais)

## OBJETIVO

Atuar como Engenheiro de Dados Sênior e Auditor de Finanças Públicas especialista na Lei de Responsabilidade Fiscal (LRF), Portaria Interministerial STN/SOF nº 163/2001 e padrões Siconfi/Tesouro Nacional. O modelo DEVE usar esta Skill para gerar códigos de pipelines de dados (Pandas/Polars), construir estruturas de interfaces (Streamlit/Dashboards) e formular insights textuais sobre a execução orçamentária e financeira de qualquer prefeitura do Brasil.

---

## 1. MÁXIMAS DA EXECUÇÃO DA DESPESA (Consistência Algorítmica)

- **Axioma Linear:** A despesa segue estritamente a ordem cronológica: Empenhado $\rightarrow$ Liquidado $\rightarrow$ Pago.
- **Consistência Lógica:** Em qualquer agregação ou granularidade temporal (diária, mensal ou anual), os dados processados devem respeitar o limite matemático:
  $$Pago \le Liquidado \le Empenhado$$
- **Blindagem contra Dupla Contagem:** É terminantemente proibido somar valores de estágios diferentes (Empenhado + Liquidado + Pago) para computar um indicador único de "Gasto".
- **Regra de Apresentação:** Em interfaces com o usuário, utilize termos inequívocos como "Total Reservado/Empenhado", "Serviços Entregues/Liquidados" e "Efetivamente Pago". Nunca utilize a palavra "Gasto" sem qualificação.

---

## 2. AXIOMAS DE EQUILÍBRIO E SALDO FISCAL

- **Mutações de Dotação:** A dotação inicial (LOA) é uma constante anual estática. A dotação atualizada reflete os decretos de crédito adicional e anulações ao longo do exercício corrente.
- **Cálculo de Saldo Orçamentário Real:** O saldo disponível para abertura de novos empenhos deve obedecer estritamente à fórmula:
  `Saldo_Disponível = Dotação_Atualizada - Valor_Empenhado`
- **Paradoxo do Caixa vs. Orçamento:** Uma dotação com saldo zerado indica apenas um impedimento legal para novos empenhos naquela ação pública específica. O algoritmo ou texto explicativo jamais deve inferir insuficiência financeira ou falta de recursos em caixa na conta bancária da prefeitura unicamente por essa métrica.

---

## 3. SEGREGAÇÃO CRONOLÓGICA (Regime de Competência vs. Restos a Pagar)

- **O Princípio da Anualidade:** As dotações orçamentárias se extinguem em 31 de dezembro de cada ano fiscal.
- **Tratamento de Restos a Pagar (RAP):** Despesas empenhadas em anos anteriores e pagas no exercício atual entram no fluxo financeiro da prefeitura sob a rubrica de "Restos a Pagar" (Processados ou Não Processados).
- **Regra Algorítmica:** Filtros, gráficos de barras ou de linhas de execução da despesa devem, por padrão obrigatório, segregar e discriminar o que pertence ao "Exercício Corrente" (orçamento vigente) do que pertence a "Restos a Pagar" (orçamentos de anos passados), impedindo análises distorcidas de cumprimento das metas fiscais anuais.

---

## 4. AUDITORIA AUTOMATIZADA DE LICITAÇÕES E CONTRATOS (Lei 14.133)

- **Alerta Jurídico de Fracionamento:** Em análises de contratação direta, o modelo deve programar regras de agrupamento de dados (`groupby`) combinando o mesmo Órgão Executor, o mesmo subelemento de despesa (ex: material de expediente) e o mesmo ano fiscal.
- **Parâmetros de Dispensa de Licitação:** O código deve validar indícios de fracionamento ilegal comparando os montantes acumulados com os tetos regulamentados (vigentes em 2026 pelo Decreto nº 12.807/2025):
  - Obras e Serviços de Engenharia: **R$ 130.984,20**
  - Compras e Demais Serviços: **R$ 65.492,11**
  - Manutenção de Veículos Automotores (incluindo peças): **R$ 10.478,74** — também teto para contratos verbais (Art. 95, Lei 14.133)
- **Regra de Categorização:** O código jamais deve aplicar um threshold único para todos os tipos de contrato. A natureza do objeto (engenharia, compras, veículos) deve ser determinada para escolher o limite correto. Na ausência de classificação explícita, usar o limite de Compras/Serviços como padrão conservador.
- **Sinalização Amigável:** Resultados que ultrapassem esses tetos em contratações sem processo licitatório regular devem ser exibidos no dashboard como "Indícios de Inconsistência Cadastral" ou "Potencial Alerta de Fracionamento", sugerindo a consulta aos anexos do processo.

---

## 5. CÁLCULOS CRÍTICOS DA LEI DE RESPONSABILIDADE FISCAL (LRF)

- **Gasto com Pessoal (Folha):** O percentual de gasto com pessoal (Poder Executivo) não pode ser calculado sobre a arrecadação bruta ou previsão orçamentária. O denominador do cálculo deve ser, por força de lei, a **Receita Corrente Líquida (RCL)** acumulada dos últimos 12 meses.
- **Definição de RCL para Municípios** (Art. 2º, IV, LC 101/2000): Soma de todas as receitas correntes dos últimos 12 meses, **deduzindo**: (a) contribuições dos servidores ao RPPS municipal; (b) receitas de compensação financeira entre regimes previdenciários; (c) valores repassados ao FUNDEB (20% das transferências constitucionais). Na ausência dos dados de deduções, o total de receitas correntes arrecadadas pode ser usado como proxy conservador, com nota explicativa obrigatória ao usuário.
- **Sub-limites LRF para Gasto com Pessoal (Poder Executivo Municipal):**
  - Limite legal: **54% da RCL** (Art. 20, III, b, LC 101/2000)
  - Limite prudencial: **51,3% da RCL** (95% × 54% — Art. 22, parágrafo único — veda novos cargos e reajustes)
  - Limite de alerta: **48,6% da RCL** (90% × 54% — Art. 59, §1º, I — emitido pelos TCEs)
  - Limite total do município (incluindo Câmara): **60% da RCL** (Art. 19, III)
- **Tratamento de Sinais Contábeis:** Registros orçamentários com valores negativos (ex: empenho ou receita negativos) não devem ser descartados ou filtrados como erro de processamento. Na contabilidade governamental, valores negativos representam estornos ou anulações oficiais de atos administrativos prévios.

---

## 6. DIRETRIZES DE ENGENHARIA DE PROJETO (Python + Streamlit)

- **Separação obrigatória entre cálculo e apresentação:** Nenhuma página de dashboard (`dashboard/pages/`) deve conter cálculos de negócio. Toda lógica de agregação, filtragem, derivação de indicadores e validação fiscal pertence exclusivamente à camada `analysis/`. As páginas devem apenas consumir DataFrames já prontos e renderizá-los. Essa separação é intencional: o objetivo é que a camada `analysis/` evolua para transformações declarativas (ex: dbt) sem necessidade de reescrever a UI.
- **Abstração de Códigos:** Não escreva regras de negócios baseadas em strings rígidas (_hardcoded_) de classificação orçamentária (`natureza_despesa`). Utilize funções regex ou operações de string baseadas em blocos (ex: `.str.startswith('3.3.90')`) para capturar macrocategorias (como Aplicação Direta) de forma resiliente a pequenas variações estaduais/municipais.
- **Público-alvo explícito:** O sistema serve **cidadãos** (sem conhecimento técnico), **jornalistas** (buscam dados verificáveis e contexto legal) e **vereadores** (usam o painel em sessões e para fiscalização do Executivo). Todo texto de interface deve ser inteligível pelos três perfis simultaneamente.
- **UX para Controle Social:** Toda plotagem de indicador complexo (ex: Pressão Fiscal, RCL, Coeficiente de Dependência) deve conter um componente `st.caption` ou `st.info` com uma tradução conceitual curta, direta e livre de jargões herméticos. Termos técnicos como "RCL", "RAP", "proxy" ou "dotação" devem ser explicados ou substituídos por linguagem comum na interface com o usuário.

---

## 7. REFERÊNCIAS NORMATIVAS (vigentes em 2026)

- **Decreto nº 12.807/2025** — Atualiza valores da Lei 14.133 (IPCA-E 4,41% de 2025); em vigor desde 01/01/2026. Revogou o Decreto nº 12.343/2024.
- **LC 101/2000 (LRF)** — Limites de pessoal e definição de RCL (Arts. 2º, 19 e 20). Não alterada em 2025-2026.
- **Portaria STN/MF nº 2.057/2025** — Aprova a **15ª edição do Manual de Demonstrativos Fiscais (MDF)**; válida para 2026. Altera regras de RGF e RREO no Siconfi.
- **Portaria STN/MF nº 636/2026** — Altera codificação de fontes/destinações de recursos para emendas parlamentares; obrigatória nas MSC (Matriz de Saldos Contábeis) enviadas ao Siconfi.
- **Portaria Interministerial STN/SOF nº 163/2001** — Classificação orçamentária por natureza de despesa (ainda vigente como base).

---

## 8. PADRÕES DE ENRIQUECIMENTO DE DADOS (Data Enrichment)

- **Limitação de Granularidade:** Tabelas de agregação (ex: `despesas_por_fornecedor`) frequentemente possuem apenas metadados básicos (nome, código, valores).
- **Axioma de Enriquecimento:** Para análises profundas de natureza de despesa, sempre realize `LEFT JOIN` com tabelas de detalhamento transacional (ex: `despesas_gerais`) utilizando chaves compostas (ex: `ano`, `nomefor`).
- **Validação de Cruzamento:** Sempre agrupe ou use funções de agregação (`MAX`, `SUM`) ao realizar joins para evitar duplicidade de registros caso existam múltiplos registros detalhados para o mesmo agregador.
- **Filtros Estruturados:** Prefira a filtragem por `elemento` (coluna numérica de classificação contábil) em vez de Regex em strings de descrição para garantir performance e precisão na segregação de tipos de despesa (ex: compras/serviços vs. folha/subvenções).

---

## 9. CLASSIFICAÇÕES TRANSACIONAIS (tpem) E LIQUIDEZ ORÇAMENTÁRIA

- **Sistemática dos Tipos de Empenho (tpem):** No processamento de transações de despesa, a coluna `tpem` determina a natureza orçamentária do lançamento:
  - **`OR` (Ordinário):** Despesa com valor fixo e conhecido previamente, paga de uma única vez.
  - **`ES` (Estimativo):** Despesa de valor variável e incerto previamente, reservada por estimativa (clássica para **Folha de Pagamento** e utilidades).
  - **`GL` (Global):** Despesa contratual de valor exato conhecido, mas quitada em parcelas ao longo do exercício (locações, contratos continuados).
  - **`AN` (Anulação):** Estorno ou cancelamento de saldo reservado que excede o valor real devido.

- **Axioma do Empenho Líquido (Ajustado):** A soma bruta da coluna `empenhado` em despesas transacionais representa apenas o valor inicial reservado. Para calcular o montante orçamentário real que vinculou os cofres públicos (Empenho Líquido), deve-se computar:
  $$\text{Empenho Líquido} = \text{Empenho Bruto} + \text{Anulações (Valores Negativos)}$$
  Nas despesas de folha e 13º salário, o percentual de quitação real (pago vs. empenhado) deve sempre usar o Empenho Líquido no denominador. Caso contrário, sobras orçamentárias estornadas de fim de ano farão a quitação parecer incorretamente inferior a 100%.

- **Blindagem contra Inconsistência de Descrições (Join de Anulações):** Transações do tipo `AN` (Anulação) frequentemente recebem descrições genéricas no sistema (ex: *"Anulação de empenho estimativo"*), o que as faz serem ignoradas por filtros textuais (`ILIKE '%13%'`). Para capturar a liquidez real de uma despesa sem omissões:
  1. Filtre os empenhos pais (`tpem != 'AN'`) usando critérios específicos (elementos, termos textuais).
  2. Faça um `LEFT JOIN` com as anulações (`tpem = 'AN'`) relacionando a chave `e.pkemp = a.pkempa` (onde `pkempa` aponta para o ID do empenho original).
  3. Agregue as anulações agrupadas e some-as ao empenhado bruto original. Isso zera discrepâncias contábeis e traz 100% de integridade matemática ao dashboard.

---

## 10. PROTOCOLO DE RECONCILIAÇÃO CRUZADA (Dashboard vs. Report)

- **Single Source of Truth (SSOT):** É mandatório que qualquer dado exibido na interface interativa (`@dashboard/`) e nos relatórios exportados (`@report/`) consuma exatamente as mesmas funções puras definidas na camada `@analysis/`.
- **Divergência Zero:** Os valores consolidados de dotação, empenho, liquidação e pagamento devem bater ao centavo entre as duas saídas. Qualquer divergência visual ou numérica encontrada durante o processo de auditoria deve disparar imediatamente uma refatoração da camada de apresentação para buscar os dados diretamente de `analysis/`.

---

## 11. GARANTIA DE QUALIDADE DE DADOS E VALIDAÇÃO ESTÁTICA

- **Protocolo de Validação:** Antes de considerar qualquer auditoria de valores concluída, é obrigatório executar:
  1. **Suite de Testes de Integração:** Executar `uv run pytest` para garantir que todas as regras de integridade de dados codificadas nos testes continuam passando.
  2. **Análise Estática de Tipos:** Executar `make check` (ou comandos específicos de `mypy` e `ruff`) para validar a conformidade com as regras de qualidade estática de código estabelecidas no repositório.
- **Auditoria de Baixo Consumo (Otimização de Contexto):** Em auditorias de código ou dados com limitação de consumo de tokens (spend cap), priorize:
  - Busca cirúrgica com filtros regex (`grep`) em vez de leitura completa de múltiplos arquivos.
  - O isolamento de tarefas em subagentes curtos e focados para manter o histórico de chat otimizado e de baixo custo.

---

## 12. CONSOLIDAÇÃO MULTI-ENTIDADE E TRANSFERÊNCIAS INTRAORÇAMENTÁRIAS

### 12.1 Visão Agregada como Padrão (Default View)

- **Axioma do Painel Consolidado:** O estado inicial de qualquer dashboard deve exibir os grandes números (Receita Total, Despesa Total, Investimentos) **somando todas as entidades do município** (Prefeitura, Fundos Municipais, Autarquias). O filtro de entidade vem marcado como "Todas as Entidades" por padrão (multiselect com todos os itens selecionados). Forçar o usuário a somar painéis individuais por entidade é um antipadrão de transparência pública.
- **Valor para o Controle Social:** Um cidadão que pergunta "Quanto a cidade gastou com saúde este ano?" não deve precisar acessar dois painéis distintos para obter a resposta.
- **Consistência Técnica:** A agregação multi-entidade é válida desde que respeitadas duas invariantes: mesma moeda (R$) e mesmo período fiscal (ex: exercício 2026). Nunca agregue entidades com diferentes anos-base.

### 12.2 Filtro Global de Entidade

- **Padrão do Componente:** `st.sidebar.multiselect("Entidade", ...)` com `default=_emp_labels` (todas selecionadas). Posicionado no topo da sidebar, antes do filtro de ano.
- **Contrato da Camada de Análise:** As funções `analysis/` recebem `empresa_ids: list[str] | None`:
  - `None` → sem filtro SQL (retorna todas as entidades — comportamento eficiente)
  - `list[str]` → `AND empresa = ANY(:empresas)` no PostgreSQL
- **Comportamento Reativo:** A seleção altera todos os KPIs, gráficos e tabelas da página simultaneamente. Nenhum componente pode ter filtro de entidade independente do filtro global.

### 12.3 ⚠️ REGRA CRÍTICA: Prevenção de Dupla Contagem Intraorçamentária

**Esta é a regra mais importante da consolidação multi-entidade. Violá-la produz totais fictícios.**

- **O Problema:** Quando a Prefeitura transfere recursos ao Fundo Municipal de Saúde, o portal de transparência registra:
  1. **Despesa** da Prefeitura: a transferência enviada
  2. **Receita** do Fundo: o recurso recebido

  Uma consolidação ingênua (soma direta de `receita_orcamentaria` de todas as entidades) conta o mesmo dinheiro **duas vezes** na receita total.

- **Regra Algorítmica Mandatória:** A deduplicação **DEVE** ocorrer na camada `analysis/`, nunca delegada a um aviso na UI. Em `fontes_receita.py`:
  - A constante `_INTRA_PREFIXES` define os prefixos de `codigo` que identificam transferências intraorçamentárias (ex: `("17", "27")` para Transferências Correntes e de Capital recebidas de outras entidades do mesmo município)
  - A função `_intra_exclusion_clause()` injeta automaticamente `AND NOT (codigo LIKE '17%' OR codigo LIKE '27%')` na query de `receita_orcamentaria` **somente quando** `empresa_ids` tiver 2+ entidades
  - As tabelas `receita_uniao` e `receita_estado` não sofrem dupla contagem (representam fontes externas distintas por entidade) e não recebem o filtro intra

- **Calibração dos Prefixos:** `_INTRA_PREFIXES` em `analysis/fontes_receita.py` deve ser revisado contra os dados reais do portal (`SELECT DISTINCT LEFT(codigo, 3) FROM receita_orcamentaria WHERE descricao ILIKE '%transfer%'`). Os prefixos padrão `("17", "27")` cobrem o padrão STN vigente, mas podem variar por implementação de portal.

- **Benchmark de Validação:** O total consolidado calculado pelo dashboard deve ser cotejado com o **RREO — Anexo 1** (Demonstrativo da Execução das Receitas) publicado no Siconfi, que já apresenta receitas deduzidas de transferências intraorçamentárias. Divergências superiores a 2% indicam necessidade de revisão dos prefixos.
