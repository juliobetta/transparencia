import fs from "node:fs";
import path from "node:path";
import { FISCAL_TAXONOMY } from "../mcp/transparencia-mcp";

export interface ContextOptions {
  portalSlug: string;
  year: number;
  domain?: string;
  currentRoute?: string;
}

export function loadSkillMarkdown(skillName: string): string {
  try {
    const filePath = path.join(
      process.cwd(),
      "apps",
      "web",
      "lib",
      "skills",
      `${skillName}.md`,
    );
    if (fs.existsSync(filePath)) {
      return fs.readFileSync(filePath, "utf-8");
    }

    // Fallback relativo para ambientes monorepo
    const relativePath = path.join(__dirname, `${skillName}.md`);
    if (fs.existsSync(relativePath)) {
      return fs.readFileSync(relativePath, "utf-8");
    }
  } catch (_e) {}
  return "";
}

export function buildLayeredContext(options: ContextOptions): string {
  const { portalSlug, year, domain, currentRoute } = options;

  // Layer 1: Contexto de Runtime Injetado
  let contextPrompt = `# CONTEXTO DE RUNTIME DO MUNICÍPIO
- Portal Slug Ativo: "${portalSlug}"
- Exercício Fiscal Selecionado: ${year}
- Rota Atual da Interface: "${currentRoute || "/visao-geral"}"
- Regra de Ouro: Todas as consultas SQL DuckDB DEVEM incluir "WHERE portal_slug = '${portalSlug}' AND ano = ${year}".
- REGRA GERAL ANTI-ALUCINAÇÃO FISCAL (TODAS AS ÁREAS):
  1. DIFERENCIAÇÃO RIGOROSA DE FASES ORÇAMENTÁRIAS: NUNCA justifique diferenças numéricas entre estágios da despesa/receita (Empenhado vs. Liquidado vs. Pago) supondo "divisões por secretarias, programas, órgãos ou rubricas" (ex: "Educação Infantil"). A diferença entre Empenhado e Liquidado representa reservas orçamentárias ainda não executadas; a diferença entre Liquidado e Pago representa restos a pagar ou retenções pendentes de repasse.
  2. PROIBIÇÃO DE HIPÓTESES SEM DADOS: NUNCA invente secretarias, categorias ou razões operacionais não explicitamente presentes nas linhas retornadas pelas queries DuckDB.
  3. VALORES ACUMULADOS NO EXERCÍCIO: Todas as métricas monetárias nos marts representam o valor ACUMULADO no exercício fiscal (ano) até o momento, NUNCA parcelas mensais isoladas.
  4. DISTINÇÃO DE ESCOPO: Ao comparar totais consolidados de um mart com subconjuntos (ex: Total Consolidado do CAPREM vs. Contribuição Patronal da Folha), explicite a diferença de escopo para não tratar o total do domínio como se fosse uma única obrigação isolada.
  5. PROIBIÇÃO DE SOMA CONTRATOS + RESTOS A PAGAR (PASSIVOS EXIGÍVEIS): NUNCA valide nem afirme que "total devido" ou "passivo financeiro" é a soma do Saldo de Contratos com Restos a Pagar. O saldo futuro a empenhar de contratos é compromisso orçamentário futuro (só vira obrigação a pagar após liquidação), NÃO dívida imediata. Além disso, parcelas executadas dos contratos já integram os Restos a Pagar, gerando DUPLA CONTAGEM. O passivo financeiro exigível refere-se estritamente a Restos a Pagar e despesas liquidadas não pagas.

`;

  // Layer 2: Skills de Domínio Específico (Markdown)
  const skillsToLoad = [
    "posicao-fiscal",
    "despesas-fornecedores",
    "saude-caprem",
    "licitacoes-contratos",
    "lrf-pessoal",
  ];

  contextPrompt += "# SKILLS E REGRAS CONTÁBEIS CANÔNICAS (STN/MCASP)\n";
  for (const skill of skillsToLoad) {
    if (!domain || skill.includes(domain.toLowerCase())) {
      const markdown = loadSkillMarkdown(skill);
      if (markdown) {
        contextPrompt += `\n--- Skill: ${skill} ---\n${markdown}\n`;
      }
    }
  }

  // Layer 3: Taxonomia de Marts Parquet Disponíveis
  contextPrompt += "\n# TAXONOMIA DOS MARTS PARQUET DISPONÍVEIS\n";
  contextPrompt +=
    "- GUIA DE CONSULTA A DIMENSÕES (dim_*): Utilize tabelas 'dim_*' para enriquecer consultas e fazer JOINs de detalhes cadastrais (ex: dim_credor para fornecedores/CPF/CNPJ, dim_elemento_despesa para elementos 30/36/39/52, dim_natureza_despesa para naturezas STN/MCASP, dim_funcao_subfuncao para funções orçamentárias e dim_orgao para secretarias).\n";
  for (const dom of FISCAL_TAXONOMY) {
    contextPrompt += `\n## Domínio: ${dom.domain}\n`;
    for (const mart of dom.marts) {
      contextPrompt += `- **${mart.table}**: ${mart.description} (Colunas: ${mart.columns.join(", ")})\n`;
    }
  }

  return contextPrompt;
}
