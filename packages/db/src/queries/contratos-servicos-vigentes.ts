import { sql } from "kysely";
import { db } from "../client";

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
}

function toIsoDateString(val: unknown): string | null {
  if (!val) return null;
  if (val instanceof Date) {
    if (Number.isNaN(val.getTime())) return null;
    const yyyy = val.getUTCFullYear();
    const mm = String(val.getUTCMonth() + 1).padStart(2, "0");
    const dd = String(val.getUTCDate()).padStart(2, "0");
    return `${yyyy}-${mm}-${dd}`;
  }
  const str = String(val).trim();
  if (str.includes("T")) return str.split("T")[0];
  if (/^\d{4}-\d{2}-\d{2}/.test(str)) return str.slice(0, 10);
  return str;
}

export async function getContratosServicosVigentes(
  portalSlug: string,
  ano?: number,
  empresaIds?: string[] | null,
): Promise<ContratoServicoVigente[]> {
  try {
    if (Array.isArray(empresaIds) && empresaIds.length === 0) {
      return [];
    }

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
      ])
      .where("portal_slug", "=", portalSlug);

    if (ano) {
      query = query.where("ano", "=", ano);
    }

    if (Array.isArray(empresaIds) && empresaIds.length > 0) {
      query = query.where("empresa_id", "in", empresaIds);
    }

    const rows = await query
      .orderBy("total_pago", "asc")
      .orderBy(sql`(total_empenhado - total_pago)`, "desc")
      .orderBy("total_empenhado", "desc")
      .execute();

    return rows.map((row: Record<string, unknown>) => {
      const totalEmpenhado = Number(row.total_empenhado ?? 0);
      const totalLiquidado = Number(row.total_liquidado ?? 0);
      const totalPago = Number(row.total_pago ?? 0);
      const valorAditado = Number(row.valor_aditado ?? 0);
      const saldoPendente = Math.max(0, totalEmpenhado - totalPago);
      const percentualPago =
        totalEmpenhado > 0 ? (totalPago / totalEmpenhado) * 100 : 0;

      return {
        contratoServicoId: row.contrato_servico_id,
        portalSlug: row.portal_slug,
        empresaId: row.empresa_id ?? undefined,
        ano: Number(row.ano ?? 0),
        contratoNumero: row.contrato_numero ?? undefined,
        fornecedorNome: row.fornecedor_nome ?? "",
        fornecedorCnpj: row.fornecedor_cnpj ?? "",
        objetoDescricao: row.objeto_descricao ?? "",
        dataInicio: toIsoDateString(row.data_inicio),
        vencimentoAtual: toIsoDateString(row.vencimento_atual),
        valorAditado: valorAditado > 0 ? valorAditado : undefined,
        totalEmpenhado,
        totalLiquidado,
        totalPago,
        saldoPendente,
        percentualPago,
      };
    });
  } catch {
    return [];
  }
}
