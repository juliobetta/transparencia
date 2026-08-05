import { sql } from "kysely";
import { db } from "../client";
import { logQueryError } from "./_log";

export const CAPREM_CODE = "1061";
export const CASP_CNPJ = "07.573.075/0001-00";

export const ELEMENTO_LABELS: Record<string, string> = {
  "13": "Contribuições Patronais",
  "46": "Auxílio-Alimentação",
  "71": "Principal da Dívida Contratual Resgatado (Parcelamento)",
  "91": "Sentenças Judiciais",
  "97": "Aporte para Cobertura do Déficit Atuarial do RPPS",
};

export interface EntityCaprem {
  entidade: string;
  empenhado: number;
  liquidado: number;
  pago: number;
  taxaExecucao: number;
}

export interface NaturezaCaprem {
  natureza: string;
  descricao: string;
  elemento: string;
  dataEmpenho?: string;
  destino: string;
  empenhado: number;
  liquidado: number;
  pago: number;
}

export interface CaspCredor {
  fornecedorNome: string;
  fornecedorCpfCnpj: string;
  totalProjetos: number;
  totalEmpenhos: number;
  empenhado: number;
  pago: number;
  alerta: string;
  alertaBadgeVariant: "warning" | "accent" | "default" | "success" | "danger";
}

export interface CadprevParcelamento {
  numeroCadprev: string;
  descricao: string;
  elemento: string;
  empenhado: number;
  pago: number;
  dataEmpenho?: string;
}

export interface MensalCaprem {
  mes: number;
  empenhado: number;
  liquidado: number;
  pago: number;
}

export interface AnnualTrendCaprem {
  ano: number;
  empenhado: number;
  liquidado: number;
  pago: number;
}

export interface ActuarialRiskSummary {
  totalAporteExigido: number;
  totalAporteQuitado: number;
  romboAporteNaoRepassado: number;
  taxaAdimplenciaAporte: number;
  totalEmpenhadoPatronal: number;
  totalPagoPatronal: number;
  romboPatronalNaoRepassado: number;
  deficitMedioMensal: number;
  totalAmortizacaoDivida: number;
  variacaoAmortizacaoPct: number;
  servidoresEfetivos: number;
  servidoresTemporariosComissionados: number;
  razaoTemporariosEfetivosPct: number;
}

export interface AnnualActuarialTrend {
  ano: number;
  aporteExigido: number;
  aporteQuitado: number;
  taxaAdimplencia: number;
  amortizacaoDivida: number;
}

export interface HistoriaCapremResult {
  entidades: EntityCaprem[];
  natureza: NaturezaCaprem[];
  caspCredores: CaspCredor[];
  cadprevParcelamentos: CadprevParcelamento[];
  mensal: MensalCaprem[];
  annualTrend: AnnualTrendCaprem[];
  actuarialRisk: ActuarialRiskSummary;
  actuarialTrend: AnnualActuarialTrend[];
  totalEmpenhado: number;
  totalLiquidado: number;
  totalPago: number;
  taxaExecucao: number;
  totalAporteAtuarial: number;
  totalDividaResgatada: number;
  totalCaspPlanoSaude: number;
}

export async function getHistoriaCaprem(
  portalSlug: string,
  year: number,
  _empresaIds?: string[] | null,
): Promise<HistoriaCapremResult> {
  const entidades: EntityCaprem[] = [];
  const natureza: NaturezaCaprem[] = [];
  const caspCredores: CaspCredor[] = [];
  const cadprevParcelamentos: CadprevParcelamento[] = [];
  const mensal: MensalCaprem[] = [];
  let annualTrend: AnnualTrendCaprem[] = [];
  const actuarialTrend: AnnualActuarialTrend[] = [];
  let totalEmpenhado = 0;
  let totalLiquidado = 0;
  let totalPago = 0;
  let totalAporteAtuarial = 0;
  let totalDividaResgatada = 0;
  let totalCaspPlanoSaude = 0;

  try {
    const q = sql`
      SELECT o.orgao_nome AS entidade,
             SUM(CASE WHEN pg_typeof(f.empenhado)::text = 'numeric' THEN f.empenhado ELSE CAST(REPLACE(f.empenhado::text, ',', '.') AS numeric) END) AS empenhado,
             SUM(CASE WHEN pg_typeof(f.liquidado)::text = 'numeric' THEN f.liquidado ELSE CAST(REPLACE(f.liquidado::text, ',', '.') AS numeric) END) AS liquidado,
             SUM(CASE WHEN pg_typeof(f.pago)::text = 'numeric' THEN f.pago ELSE CAST(REPLACE(f.pago::text, ',', '.') AS numeric) END) AS pago
      FROM fct_despesas_por_fornecedor f
      JOIN dim_orgao o ON o.empresa_id = f.empresa::text AND o.portal_slug = ${portalSlug}
      WHERE (f.codigo = ${CAPREM_CODE} OR f.descricao ILIKE '%CAPREM%' OR f.descricao ILIKE '%CASP%' OR f.fornecedor_cpf_cnpj = ${CASP_CNPJ}) AND f.ano = ${year}
      GROUP BY o.orgao_nome
      ORDER BY empenhado DESC NULLS LAST
    `;
    const resE = await q.execute(db);

    for (const r of (resE.rows as Record<string, unknown>[]) || []) {
      const emp = parseFloat(String(r.empenhado ?? "0")) || 0;
      const liq = parseFloat(String(r.liquidado ?? "0")) || 0;
      const pag = parseFloat(String(r.pago ?? "0")) || 0;
      totalEmpenhado += emp;
      totalLiquidado += liq;
      totalPago += pag;
      entidades.push({
        entidade: String(r.entidade ?? ""),
        empenhado: emp,
        liquidado: liq,
        pago: pag,
        taxaExecucao: emp > 0 ? (pag / emp) * 100 : 0,
      });
    }
  } catch (error) {
    logQueryError("getHistoriaCaprem", error);
  }

  let totalEmpenhadoPatronal = 0;
  let totalPagoPatronal = 0;

  try {
    const qN = sql`
      SELECT elemento,
             natureza_despesa AS natureza,
             fornecedor_nome,
             fornecedor_cpf_cnpj,
             MAX(data_empenho::text) AS data_empenho,
             MAX(descricao) AS descricao,
             SUM(CAST(empenhado AS numeric)) AS empenhado,
             SUM(CAST(liquidado AS numeric)) AS liquidado,
             SUM(CAST(pago AS numeric)) AS pago
      FROM fct_despesas
      WHERE portal_slug = ${portalSlug}
        AND ano = ${year}
        AND (fornecedor_nome ILIKE '%CAPREM%' OR fornecedor_nome ILIKE '%CASP%' OR fornecedor_cpf_cnpj = ${CASP_CNPJ} OR descricao ILIKE '%CASP%' OR elemento IN ('97', '71', '13'))
        AND (tipo_empenho IS NULL OR tipo_empenho != 'AN')
        AND elemento IS NOT NULL AND elemento != ''
      GROUP BY elemento, natureza_despesa, fornecedor_nome, fornecedor_cpf_cnpj
      ORDER BY empenhado DESC
    `;
    const resN = await qN.execute(db);

    for (const r of (resN.rows as Record<string, unknown>[]) || []) {
      const el = String(r.elemento ?? "");
      const emp = parseFloat(String(r.empenhado ?? "0")) || 0;
      const liq = parseFloat(String(r.liquidado ?? "0")) || 0;
      const pag = parseFloat(String(r.pago ?? "0")) || 0;
      const dtEmp = String(r.data_empenho ?? "");
      const rawForn = String(r.fornecedor_nome ?? "").toUpperCase();
      const rawNat = String(
        r.natureza_despesa ?? String(r.natureza ?? ""),
      ).toUpperCase();
      const rawDesc = String(r.descricao ?? "").toUpperCase();
      const rawCnpj = String(r.fornecedor_cpf_cnpj ?? "");

      const natLabel =
        ELEMENTO_LABELS[el] || String(r.natureza ?? "") || `Elemento ${el}`;

      let destino = "Encargo Patronal Geral";
      if (el === "97") {
        destino = "Aporte Atuarial (CAPREM)";
      } else if (el === "71") {
        destino = "Amortização Dívida (CAPREM)";
      } else if (
        rawForn.includes("CASP") ||
        rawNat.includes("CASP") ||
        rawDesc.includes("CASP") ||
        rawCnpj === CASP_CNPJ
      ) {
        destino = "Plano de Saúde (CASP)";
      } else if (
        rawForn.includes("CAPREM") ||
        rawNat.includes("RPPS") ||
        rawNat.includes("CAPREM") ||
        rawDesc.includes("CAPREM")
      ) {
        destino = "RPPS (CAPREM)";
      } else if (
        rawForn.includes("INSS") ||
        rawForn.includes("RECEITA FEDERAL") ||
        rawForn.includes("SEGURO SOCIAL") ||
        rawNat.includes("INSS") ||
        rawNat.includes("RGPS")
      ) {
        destino = "INSS (RGPS)";
      }

      natureza.push({
        natureza: natLabel,
        descricao: natLabel,
        elemento: el,
        dataEmpenho: dtEmp,
        destino,
        empenhado: emp,
        liquidado: liq,
        pago: pag,
      });

      if (el === "97") {
        totalAporteAtuarial += emp;
      }
      if (el === "71") {
        totalDividaResgatada += emp;
      }
      if (destino === "Plano de Saúde (CASP)") {
        totalCaspPlanoSaude += emp;
      }
      if (el === "13" && destino === "RPPS (CAPREM)") {
        totalEmpenhadoPatronal += emp;
        totalPagoPatronal += pag;
      }
    }
  } catch (error) {
    logQueryError("getHistoriaCaprem", error);
  }

  // Busca de Acordos de Parcelamento CADPREV
  try {
    const qCad = sql`
      SELECT elemento,
             descricao,
             MAX(data_empenho::text) AS data_empenho,
             SUM(CAST(empenhado AS numeric)) AS empenhado,
             SUM(CAST(pago AS numeric)) AS pago
      FROM fct_despesas
      WHERE portal_slug = ${portalSlug}
        AND ano = ${year}
        AND (
          descricao ILIKE '%CADPREV%'
          OR descricao ILIKE '%PARCELA%'
          OR descricao ILIKE '%CONFISSÃO%'
          OR descricao ILIKE '%CONFISSAO%'
        )
        AND (fornecedor_nome ILIKE '%CAPREM%' OR elemento = '71')
      GROUP BY elemento, descricao
      ORDER BY empenhado DESC
    `;
    const resCad = await qCad.execute(db);

    for (const r of (resCad.rows as Record<string, unknown>[]) || []) {
      const desc = String(r.descricao ?? "");
      const el = String(r.elemento ?? "");
      const emp = parseFloat(String(r.empenhado ?? "0")) || 0;
      const pag = parseFloat(String(r.pago ?? "0")) || 0;
      const dt = String(r.data_empenho ?? "");

      let numCad = "Acordo de Parcelamento Previdenciário";
      const uDesc = desc.toUpperCase();
      if (uDesc.includes("CADPREV")) {
        const idx = uDesc.indexOf("CADPREV");
        const snippet = desc.substring(idx, idx + 22);
        numCad = snippet.replace(/[^A-Za-z0-9º/\s-]/g, "").trim();
      }

      cadprevParcelamentos.push({
        numeroCadprev: numCad,
        descricao: desc,
        elemento: el,
        empenhado: emp,
        pago: pag,
        dataEmpenho: dt,
      });
    }
  } catch (error) {
    logQueryError("getHistoriaCaprem", error);
  }

  // Busca Estrutural Contábil da CASP (Subfunções da Saúde 301, 302, 303, 304, 305 ou CNPJ CASP)
  try {
    const qC = sql`
      SELECT fornecedor_nome,
             fornecedor_cpf_cnpj,
             COUNT(DISTINCT projeto_atividade_nome) AS total_projetos,
             COUNT(DISTINCT empenho_id) AS total_empenhos,
             SUM(CAST(empenhado AS numeric)) AS empenhado,
             SUM(CAST(pago AS numeric)) AS pago
      FROM fct_despesas
      WHERE portal_slug = ${portalSlug}
        AND ano = ${year}
        AND (
          fornecedor_cpf_cnpj = ${CASP_CNPJ}
          OR (
            subfuncao IN ('301', '302', '303', '304', '305')
            AND elemento IN ('36', '39')
            AND (descricao ILIKE '%MÉDIC%' OR descricao ILIKE '%MEDIC%' OR descricao ILIKE '%CLINIC%' OR descricao ILIKE '%CLÍNICA%' OR descricao ILIKE '%EXAME%' OR descricao ILIKE '%DENTIS%' OR descricao ILIKE '%PLANO DE SAÚDE%')
          )
        )
        AND fornecedor_nome IS NOT NULL AND fornecedor_nome != ''
      GROUP BY fornecedor_nome, fornecedor_cpf_cnpj
      ORDER BY empenhado DESC
      LIMIT 10
    `;
    const resC = await qC.execute(db);

    for (const r of (resC.rows as Record<string, unknown>[]) || []) {
      const nome = String(r.fornecedor_nome ?? "").toUpperCase();
      const rawNome = String(r.fornecedor_nome ?? "");
      const cpfCnpj = String(r.fornecedor_cpf_cnpj ?? "");
      const totalProjetos = Number(r.total_projetos ?? 1);
      const totalEmpenhos = Number(r.total_empenhos ?? 1);
      const emp = parseFloat(String(r.empenhado ?? "0")) || 0;
      const pag = parseFloat(String(r.pago ?? "0")) || 0;

      const isPF =
        cpfCnpj.includes(".XXX.XXX-") ||
        nome.includes(" - ME") ||
        nome.includes(" EIRELI") ||
        nome.includes(" UNIPESSOAL");

      let alerta = "Em Conformidade";
      let alertaBadgeVariant:
        | "warning"
        | "accent"
        | "default"
        | "success"
        | "danger" = "success";

      if (
        nome.includes("CASP") ||
        nome.includes("PREFEITURA") ||
        nome.includes("CAIXA ASSIST") ||
        cpfCnpj === CASP_CNPJ
      ) {
        alerta = "Entidade Gestora";
        alertaBadgeVariant = "default";
      } else if (nome.includes("CODESP")) {
        alerta = "Consórcio Intermunicipal";
        alertaBadgeVariant = "accent";
      } else if (isPF && totalProjetos > 1) {
        alerta = `Atenção: ${totalProjetos} Projetos Concomitantes`;
        alertaBadgeVariant = "warning";
      } else if (isPF) {
        alerta = "Contratação Direta (Pessoa Física)";
        alertaBadgeVariant = "default";
      } else if (totalProjetos > 1) {
        alerta = "Clínica / PJ Multiprojeto";
        alertaBadgeVariant = "default";
      }

      caspCredores.push({
        fornecedorNome: rawNome,
        fornecedorCpfCnpj: cpfCnpj,
        totalProjetos,
        totalEmpenhos,
        empenhado: emp,
        pago: pag,
        alerta,
        alertaBadgeVariant,
      });
    }
  } catch (error) {
    logQueryError("getHistoriaCaprem", error);
  }

  // Série Histórica Atuarial (2021-2026) para o Elemento 97 (Aporte) e Elemento 71 (Dívida Resgatada)
  try {
    const qAct = sql`
      SELECT ano,
             SUM(CASE WHEN elemento = '97' THEN CAST(empenhado AS numeric) ELSE 0 END) AS aporte_exigido,
             SUM(CASE WHEN elemento = '97' THEN CAST(pago AS numeric) ELSE 0 END) AS aporte_quitado,
             SUM(CASE WHEN elemento = '71' THEN CAST(pago AS numeric) ELSE 0 END) AS amortizacao_divida
      FROM fct_despesas
      WHERE portal_slug = ${portalSlug}
        AND ano BETWEEN 2021 AND 2026
        AND elemento IN ('97', '71')
      GROUP BY ano
      ORDER BY ano
    `;
    const resAct = await qAct.execute(db);

    for (const r of (resAct.rows as Record<string, unknown>[]) || []) {
      const a = Number(r.ano);
      const exig = parseFloat(String(r.aporte_exigido ?? "0")) || 0;
      const quit = parseFloat(String(r.aporte_quitado ?? "0")) || 0;
      const amort = parseFloat(String(r.amortizacao_divida ?? "0")) || 0;
      const taxa = exig > 0 ? (quit / exig) * 100 : 100;

      actuarialTrend.push({
        ano: a,
        aporteExigido: exig,
        aporteQuitado: quit,
        taxaAdimplencia: taxa,
        amortizacaoDivida: amort,
      });
    }
  } catch (error) {
    logQueryError("getHistoriaCaprem", error);
  }

  // Contagem de Servidores Efetivos x Temporários/Comissionados
  let servidoresEfetivos = 0;
  let servidoresTemporariosComissionados = 0;
  try {
    const qP = sql`
      SELECT
        SUM(CASE WHEN categoria_funcional ILIKE '%efetiv%' AND categoria_funcional NOT ILIKE '%cedido%' THEN 1 ELSE 0 END) AS efetivos,
        SUM(CASE WHEN categoria_funcional ILIKE '%comissionad%' OR categoria_funcional ILIKE '%contrata%' OR categoria_funcional ILIKE '%excepcional%' THEN 1 ELSE 0 END) AS temporarios
      FROM fct_pessoal
      WHERE portal_slug = ${portalSlug} AND ano = ${year}
    `;
    const resP = await qP.execute(db);
    const rowP = (resP.rows as Record<string, unknown>[])?.[0];
    if (rowP) {
      servidoresEfetivos = Number(rowP.efetivos ?? 0);
      servidoresTemporariosComissionados = Number(rowP.temporarios ?? 0);
    }
  } catch (error) {
    logQueryError("getHistoriaCaprem", error);
  }

  try {
    const qM = sql`
      SELECT mes,
             SUM(CAST(empenhado AS numeric)) AS empenhado,
             SUM(CAST(liquidado AS numeric)) AS liquidado,
             SUM(CAST(pago AS numeric)) AS pago
      FROM fct_despesas
      WHERE portal_slug = ${portalSlug}
        AND ano = ${year}
        AND (fornecedor_nome ILIKE '%CAPREM%' OR fornecedor_nome ILIKE '%CASP%' OR fornecedor_cpf_cnpj = ${CASP_CNPJ} OR elemento IN ('97', '71'))
        AND (tipo_empenho IS NULL OR tipo_empenho != 'AN')
      GROUP BY mes
      ORDER BY mes
    `;
    const resM = await qM.execute(db);

    for (const r of (resM.rows as Record<string, unknown>[]) || []) {
      const m = Number(r.mes);
      const emp = parseFloat(String(r.empenhado ?? "0")) || 0;
      const liq = parseFloat(String(r.liquidado ?? "0")) || 0;
      const pag = parseFloat(String(r.pago ?? "0")) || 0;
      mensal.push({
        mes: m,
        empenhado: emp,
        liquidado: liq,
        pago: pag,
      });
    }
  } catch (error) {
    logQueryError("getHistoriaCaprem", error);
  }

  try {
    const resA = await sql`
      SELECT f.ano,
             SUM(CASE WHEN pg_typeof(f.empenhado)::text = 'numeric' THEN f.empenhado ELSE CAST(REPLACE(f.empenhado::text, ',', '.') AS numeric) END) AS empenhado,
             SUM(CASE WHEN pg_typeof(f.liquidado)::text = 'numeric' THEN f.liquidado ELSE CAST(REPLACE(f.liquidado::text, ',', '.') AS numeric) END) AS liquidado,
             SUM(CASE WHEN pg_typeof(f.pago)::text = 'numeric' THEN f.pago ELSE CAST(REPLACE(f.pago::text, ',', '.') AS numeric) END) AS pago
      FROM fct_despesas_por_fornecedor f
      JOIN dim_orgao o ON o.empresa_id = f.empresa::text AND o.portal_slug = ${portalSlug}
      WHERE (f.codigo = ${CAPREM_CODE} OR f.descricao ILIKE '%CAPREM%' OR f.descricao ILIKE '%CASP%' OR f.fornecedor_cpf_cnpj = ${CASP_CNPJ})
      GROUP BY f.ano
      ORDER BY f.ano
    `.execute(db);

    annualTrend = ((resA.rows as Record<string, unknown>[]) || []).map((r) => ({
      ano: Number(r.ano),
      empenhado: parseFloat(String(r.empenhado ?? "0")) || 0,
      liquidado: parseFloat(String(r.liquidado ?? "0")) || 0,
      pago: parseFloat(String(r.pago ?? "0")) || 0,
    }));
  } catch (error) {
    logQueryError("getHistoriaCaprem", error);
  }

  const taxaExecucao = totalEmpenhado > 0 ? totalPago / totalEmpenhado : 0;

  // Resumo de Risco Atuarial
  const currTrend = actuarialTrend.find((t) => t.ano === year);
  const prevTrend = actuarialTrend.find((t) => t.ano === year - 1);

  const totalAporteExigido = currTrend?.aporteExigido ?? 0;
  const totalAporteQuitado = currTrend?.aporteQuitado ?? 0;
  const romboAporteNaoRepassado = Math.max(
    0,
    totalAporteExigido - totalAporteQuitado,
  );
  const taxaAdimplenciaAporte =
    totalAporteExigido > 0
      ? (totalAporteQuitado / totalAporteExigido) * 100
      : 100;

  const romboPatronalNaoRepassado = Math.max(
    0,
    totalEmpenhadoPatronal - totalPagoPatronal,
  );
  const currentYear = new Date().getFullYear();
  const mesesDecorridos =
    year < currentYear ? 12 : Math.max(1, new Date().getMonth() + 1);
  const deficitMedioMensal =
    romboPatronalNaoRepassado > 0
      ? romboPatronalNaoRepassado / mesesDecorridos
      : 0;

  const totalAmortizacaoDivida = currTrend?.amortizacaoDivida ?? 0;
  const prevAmort = prevTrend?.amortizacaoDivida ?? 0;
  const variacaoAmortizacaoPct =
    prevAmort > 0
      ? ((totalAmortizacaoDivida - prevAmort) / prevAmort) * 100
      : totalAmortizacaoDivida > 0
        ? 100
        : 0;

  const razaoTemporariosEfetivosPct =
    servidoresEfetivos > 0
      ? (servidoresTemporariosComissionados / servidoresEfetivos) * 100
      : 0;

  const actuarialRisk: ActuarialRiskSummary = {
    totalAporteExigido,
    totalAporteQuitado,
    romboAporteNaoRepassado,
    taxaAdimplenciaAporte,
    totalEmpenhadoPatronal,
    totalPagoPatronal,
    romboPatronalNaoRepassado,
    deficitMedioMensal,
    totalAmortizacaoDivida,
    variacaoAmortizacaoPct,
    servidoresEfetivos,
    servidoresTemporariosComissionados,
    razaoTemporariosEfetivosPct,
  };

  return {
    entidades,
    natureza,
    caspCredores,
    cadprevParcelamentos,
    mensal,
    annualTrend,
    actuarialRisk,
    actuarialTrend,
    totalEmpenhado,
    totalLiquidado,
    totalPago,
    taxaExecucao,
    totalAporteAtuarial,
    totalDividaResgatada,
    totalCaspPlanoSaude,
  };
}
