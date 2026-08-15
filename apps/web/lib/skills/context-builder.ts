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
  for (const dom of FISCAL_TAXONOMY) {
    contextPrompt += `\n## Domínio: ${dom.domain}\n`;
    for (const mart of dom.marts) {
      contextPrompt += `- **${mart.table}**: ${mart.description} (Colunas: ${mart.columns.join(", ")})\n`;
    }
  }

  return contextPrompt;
}
