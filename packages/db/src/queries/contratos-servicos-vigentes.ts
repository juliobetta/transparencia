import { db } from "../client";

export type StatusExecucaoContrato =
  | "em_execucao"
  | "concluido"
  | "inexecutado";

export interface ContratoServicoVigente {
  contratoServicoId?: string;
  portalSlug: string;
  empresaId?: string;
  ano?: number;
  contratoNumero?: string;
  fornecedorNome: string;
  fornecedorCnpj: string;
  objetoDescricao: string;
  dataInicio: string | null;
  vencimentoAtual: string | null;
  valorAditado?: number;
  totalEmpenhado: number;
  totalLiquidado: number;
  totalPago: number;
  saldoPendente: number;
  percentualPago: number;
  statusExecucao: StatusExecucaoContrato;
}

export interface DeriveStatusExecucaoOptions {
  vencimentoAtual: string | null;
  totalEmpenhado: number;
  totalLiquidado: number;
  totalPago: number;
  ano?: number;
  referenceDateISO?: string;
}

export function deriveStatusExecucao(
  options: DeriveStatusExecucaoOptions,
): StatusExecucaoContrato {
  const {
    vencimentoAtual,
    totalEmpenhado,
    totalLiquidado,
    totalPago,
    ano,
    referenceDateISO,
  } = options;

  const now = new Date();
  const defaultRefDate = `${now.getFullYear()}-${String(now.getMonth() + 1).padStart(2, "0")}-${String(now.getDate()).padStart(2, "0")}`;
  const refDateStr = referenceDateISO || defaultRefDate;
  const isVencido = Boolean(vencimentoAtual && vencimentoAtual < refDateStr);
  const currentYear =
    Number.parseInt(refDateStr.slice(0, 4), 10) || now.getFullYear();
  const isAnoPassado = Boolean(ano && ano < currentYear);

  if (totalLiquidado <= 0 && totalPago <= 0 && (isVencido || isAnoPassado)) {
    return "inexecutado";
  }

  const percentualPago =
    totalEmpenhado > 0 ? (totalPago / totalEmpenhado) * 100 : 0;
  if (
    percentualPago >= 99.9 ||
    (totalEmpenhado > 0 && totalEmpenhado - totalPago <= 0) ||
    (isVencido && totalPago > 0 && totalLiquidado >= totalEmpenhado)
  ) {
    return "concluido";
  }

  return "em_execucao";
}

function toIsoDateString(val: unknown): string | null {
  if (!val) return null;
  if (val instanceof Date) return val.toISOString().slice(0, 10);
  const str = String(val);
  if (/^\d{4}-\d{2}-\d{2}/.test(str)) return str.slice(0, 10);
  return null;
}

export async function getContratosServicosVigentes(
  portalSlug: string,
  ano: number,
): Promise<ContratoServicoVigente[]> {
  try {
    const rows = await db
      .selectFrom("fct_contratos_servicos_vigentes")
      .select([
        "contrato_servico_id",
        "portal_slug",
        "empresa_id",
        "ano",
        "contrato_numero",
        "fornecedor_nome",
        "objeto_descricao",
        "data_inicio",
        "vencimento_atual",
        "valor_aditado",
        "total_empenhado",
        "total_liquidado",
        "total_pago",
        "status_execucao",
      ])
      .where("portal_slug", "=", portalSlug);

    return rows.map((row: Record<string, unknown>) => {
      const totalEmpenhado = Number(row.total_empenhado ?? 0);
      const totalLiquidado = Number(row.total_liquidado ?? 0);
      const totalPago = Number(row.total_pago ?? 0);
      const valorAditado = Number(row.valor_aditado ?? 0);
      const saldoPendente = Math.max(0, totalEmpenhado - totalPago);
      const percentualPago =
        totalEmpenhado > 0 ? (totalPago / totalEmpenhado) * 100 : 0;

      const vencimentoAtualStr = toIsoDateString(row.vencimento_atual);
      const rowAno = Number(row.ano ?? 0);
      const rawStatus = row.status_execucao
        ? String(row.status_execucao)
        : null;
      const statusExecucao: StatusExecucaoContrato =
        rawStatus === "inexecutado" ||
        rawStatus === "concluido" ||
        rawStatus === "em_execucao"
          ? rawStatus
          : deriveStatusExecucao({
              vencimentoAtual: vencimentoAtualStr,
              totalEmpenhado,
              totalLiquidado,
              totalPago,
              ano: rowAno > 0 ? rowAno : ano,
            });

      return {
        contratoServicoId:
          row.contrato_servico_id != null
            ? String(row.contrato_servico_id)
            : undefined,
        portalSlug: row.portal_slug != null ? String(row.portal_slug) : "",
        empresaId: row.empresa_id != null ? String(row.empresa_id) : undefined,
        ano: rowAno,
        contratoNumero:
          row.contrato_numero != null ? String(row.contrato_numero) : undefined,
        fornecedorNome:
          row.fornecedor_nome != null ? String(row.fornecedor_nome) : "",
        fornecedorCnpj:
          row.fornecedor_cnpj != null ? String(row.fornecedor_cnpj) : "",
        objetoDescricao:
          row.objeto_descricao != null ? String(row.objeto_descricao) : "",
        dataInicio: toIsoDateString(row.data_inicio),
        vencimentoAtual: vencimentoAtualStr,
        valorAditado: valorAditado > 0 ? valorAditado : undefined,
        totalEmpenhado,
        totalLiquidado,
        totalPago,
        saldoPendente,
        percentualPago,
        statusExecucao,
      };
    });
  } catch {
    return [];
  }
}
