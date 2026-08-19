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
  empresaIds?: string[],
): Promise<ContratoServicoVigente[]> {
  try {
    let query = db
      .selectFrom("fct_contratos_servicos_vigentes")
      .select([
        "contrato_servico_id",
        "portal_slug",
        "empresa_id",
        "ano",
        "contrato_numero",
        "fornecedor_nome",
        "fornecedor_cnpj",
        "objeto_descricao",
        "data_inicio",
        "vencimento_atual",
        "valor_aditado",
        "total_empenhado",
        "total_liquidado",
        "total_pago",
        "status_execucao",
      ])
      .where("portal_slug", "=", portalSlug)
      .where("ano", "=", ano);

    if (empresaIds && empresaIds.length > 0) {
      query = query.where("empresa_id", "in", empresaIds);
    }

    const rows = await query.execute();

    return rows.map((row) => {
      const totalEmpenhado = Number(row.total_empenhado ?? 0);
      const totalLiquidado = Number(row.total_liquidado ?? 0);
      const totalPago = Number(row.total_pago ?? 0);
      const valorAditado = Number(row.valor_aditado ?? 0);
      const saldoPendente = Math.max(0, totalEmpenhado - totalPago);
      const percentualPago =
        totalEmpenhado > 0 ? (totalPago / totalEmpenhado) * 100 : 0;

      const vencimentoAtualStr = toIsoDateString(row.vencimento_atual);
      const rowAno = Number(row.ano ?? 0);
      const rawStatus = row.status_execucao ? String(row.status_execucao) : "";
      const statusExecucao: StatusExecucaoContrato =
        rawStatus === "inexecutado" || rawStatus === "concluido"
          ? rawStatus
          : "em_execucao";

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
