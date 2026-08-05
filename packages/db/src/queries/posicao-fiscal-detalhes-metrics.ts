import { db } from "../client";

export interface PosicaoFiscalDetalhesMetricsDTO {
  portalSlug: string;
  ano: number;
  restosPendentesTotal: number;
  restosPendentesAnteriores: number;
  restosPendentes: Array<{
    ano: number;
    administracao: "Adm. Anterior" | "Adm. Atual";
    empenhado: number;
    pago: number;
    pendente: number;
  }>;
  topCredoresAdmAtual: Array<{
    fornecedor: string;
    pendente: number;
  }>;
  totalCredoresAdmAtual: number;
}

export async function getPosicaoFiscalDetalhesMetrics(
  portalSlug: string,
  ano: number,
  empresaIds: string[],
): Promise<PosicaoFiscalDetalhesMetricsDTO> {
  if (empresaIds.length === 0) {
    return {
      portalSlug,
      ano,
      restosPendentesTotal: 0,
      restosPendentesAnteriores: 0,
      restosPendentes: [],
      topCredoresAdmAtual: [],
      totalCredoresAdmAtual: 0,
    };
  }

  const results = await db
    .selectFrom("fct_posicao_fiscal_detalhes_metricas")
    .select([
      "portal_slug",
      "ano",
      "fornecedor_nome",
      "valor_pendente",
      "administracao",
    ])
    .where("portal_slug", "=", portalSlug)
    .where("ano", "<=", ano)
    .where("empresa_id", "in", empresaIds)
    .execute();

  const byYear = new Map<
    number,
    {
      ano: number;
      administracao: "Adm. Anterior" | "Adm. Atual";
      pendente: number;
    }
  >();

  const creditorMap = new Map<string, number>();

  for (const row of results) {
    const rowAno = Number(row.ano);
    const pendente = Number(row.valor_pendente ?? 0);
    const administracao =
      row.administracao === "Adm. Anterior" ? "Adm. Anterior" : "Adm. Atual";

    const currentYearEntry = byYear.get(rowAno) ?? {
      ano: rowAno,
      administracao,
      pendente: 0,
    };
    currentYearEntry.pendente += pendente;
    byYear.set(rowAno, currentYearEntry);

    if (administracao === "Adm. Atual") {
      const supplier = String(
        row.fornecedor_nome ?? "Sem identificação",
      ).trim();
      creditorMap.set(supplier, (creditorMap.get(supplier) ?? 0) + pendente);
    }
  }

  const restosPendentes = Array.from(byYear.values())
    .sort((a, b) => a.ano - b.ano)
    .map((item) => ({
      ano: item.ano,
      administracao: item.administracao,
      empenhado: 0,
      pago: 0,
      pendente: item.pendente,
    }));

  const credoresAdmAtual = Array.from(creditorMap.entries())
    .filter(([, pendente]) => pendente > 0)
    .map(([fornecedor, pendente]) => ({ fornecedor, pendente }))
    .sort(
      (a, b) =>
        b.pendente - a.pendente ||
        a.fornecedor.localeCompare(b.fornecedor, "pt-BR"),
    );

  const topCredoresAdmAtual = credoresAdmAtual.slice(0, 5);

  const restosPendentesTotal =
    restosPendentes.find((item) => item.ano === ano)?.pendente ?? 0;
  const restosPendentesAnteriores = restosPendentes
    .filter((item) => item.ano < ano)
    .reduce((acc, item) => acc + item.pendente, 0);

  return {
    portalSlug,
    ano,
    restosPendentesTotal,
    restosPendentesAnteriores,
    restosPendentes,
    topCredoresAdmAtual,
    totalCredoresAdmAtual: credoresAdmAtual.length,
  } satisfies PosicaoFiscalDetalhesMetricsDTO;
}
