export interface BenchmarkQuestion {
  id: string;
  domain: string;
  question: string;
  expectedMart: string;
  expectedMetrics: string[];
}

export const BENCHMARK_QUESTIONS: BenchmarkQuestion[] = [
  // 1. Posição Fiscal
  {
    id: "eval-01",
    domain: "Posição Fiscal",
    question: "Qual o total arrecadado e despesas pagas em 2025?",
    expectedMart: "fct_posicao_fiscal_metricas",
    expectedMetrics: ["total_arrecadado", "despesas_pagas"],
  },
  {
    id: "eval-02",
    domain: "Posição Fiscal",
    question: "Quanto a prefeitura tem em saldo estimado para 2025?",
    expectedMart: "fct_posicao_fiscal_metricas",
    expectedMetrics: ["saldo_estimado"],
  },
  {
    id: "eval-03",
    domain: "Posição Fiscal",
    question: "Qual o valor de restos a pagar pendentes da gestão anterior?",
    expectedMart: "fct_posicao_fiscal_metricas",
    expectedMetrics: ["restos_pendentes_adm_anterior"],
  },

  // 2. Despesas e Credores
  {
    id: "eval-04",
    domain: "Despesas e Credores",
    question: "Quanto foi empenhado e pago para os principais fornecedores?",
    expectedMart: "fct_analise_despesas_metricas",
    expectedMetrics: ["total_empenhado", "total_pago"],
  },
  {
    id: "eval-05",
    domain: "Despesas e Credores",
    question: "Existe algum contrato ou despesa vinculada à empresa ESN?",
    expectedMart: "fct_contratos_servicos_vigentes",
    expectedMetrics: ["total_pago"],
  },

  // 3. Receitas e Emendas
  {
    id: "eval-06",
    domain: "Receitas e Emendas",
    question: "Qual foi a receita prevista total e o arrecadado em 2025?",
    expectedMart: "fct_fontes_receita_metricas",
    expectedMetrics: ["total_previsto", "total_arrecadado"],
  },
  {
    id: "eval-07",
    domain: "Receitas e Emendas",
    question: "Quanto o município arrecadou em emendas PIX?",
    expectedMart: "fct_fontes_receita_metricas",
    expectedMetrics: ["emendas_pix_arrecadado"],
  },

  // 4. Saúde e CAPREM
  {
    id: "eval-08",
    domain: "Saúde e CAPREM",
    question: "Quanto a prefeitura liquidou e pagou na área de Saúde?",
    expectedMart: "fct_historia_saude_metricas",
    expectedMetrics: ["total_liquidado", "total_pago"],
  },
  {
    id: "eval-09",
    domain: "Saúde e CAPREM",
    question: "Qual o valor da retenção patronal empenhada para o CAPREM?",
    expectedMart: "fct_historia_caprem_metricas",
    expectedMetrics: ["total_empenhado_patronal"],
  },

  // 5. Licitações e Pessoal
  {
    id: "eval-10",
    domain: "Licitações e Pessoal",
    question: "Quanto foi pago com folha de pessoal no exercício?",
    expectedMart: "fct_pessoal_folha_metricas",
    expectedMetrics: ["total_folha", "total_pago"],
  },
  {
    id: "eval-11",
    domain: "Despesas e Credores",
    question:
      "Quanto foi gasto com merenda escolar em 2025 e 2026? Retorne valor empenhado e pago para os dois anos.",
    expectedMart: "fct_despesas",
    expectedMetrics: ["empenhado", "pago"],
  },
  {
    id: "eval-12",
    domain: "Saúde e CAPREM",
    question:
      "Qual o valor da obrigação patronal empenhada e o rombo patronal não repassado ao CAPREM em 2026?",
    expectedMart: "fct_historia_caprem_metricas",
    expectedMetrics: [
      "total_empenhado_patronal",
      "rombo_patronal_nao_repassado",
    ],
  },
  {
    id: "eval-13",
    domain: "Licitações e Pessoal",
    question:
      "Qual a quantidade de servidores efetivos ocupando cargos de chefia ou confiança (FG e CC) em 2026?",
    expectedMart: "fct_pessoal_folha_metricas",
    expectedMetrics: ["efetivos_confianca", "comissionados_externos"],
  },
  {
    id: "eval-14",
    domain: "Licitações e Pessoal",
    question: "Qual a porcentagem de cargos efetivos em posição de chefia?",
    expectedMart: "fct_pessoal_folha_metricas",
    expectedMetrics: ["efetivos_confianca"],
  },
  {
    id: "eval-15",
    domain: "Licitações e Pessoal",
    question:
      "Qual a vigência do contrato com a empresa L.philippe Construcoes Ltda em 2026?",
    expectedMart: "fct_contratos_servicos_vigentes",
    expectedMetrics: ["vencimento_atual", "data_inicio"],
  },
];
