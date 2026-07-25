import { sql } from "kysely";
import { db } from "../client";

export interface PortalConfig {
  portal_slug: string;
  display_name: string;
  uf: string;
  portal_url: string;
  base_host: string;
  cidade_clean: string;
  ano_inicial: number;
  empresa_padrao: string;
  brasao_asset: string;
  data_extracao: string;
}

export interface EntidadeItem {
  id: string;
  nome: string;
}

export async function getPortalConfig(
  portalSlug = "porciuncula_prefeitura",
): Promise<PortalConfig | null> {
  try {
    const result = await sql<PortalConfig>`
      select * from dim_portais where portal_slug = ${portalSlug} limit 1
    `.execute(db);

    if (result.rows.length > 0) {
      const row = result.rows[0];
      let dataExtracaoStr = "";

      if (row.data_extracao) {
        if (
          typeof row.data_extracao === "object" &&
          "toISOString" in (row.data_extracao as Record<string, unknown>)
        ) {
          dataExtracaoStr = (row.data_extracao as unknown as Date)
            .toISOString()
            .split("T")[0];
        } else {
          dataExtracaoStr = String(row.data_extracao);
        }
      }

      return {
        portal_slug: String(row.portal_slug || ""),
        display_name: String(row.display_name || ""),
        uf: String(row.uf || ""),
        portal_url: String(row.portal_url || ""),
        base_host: String(row.base_host || ""),
        cidade_clean: String(row.cidade_clean || ""),
        ano_inicial: Number(row.ano_inicial) || new Date().getFullYear(),
        empresa_padrao: String(row.empresa_padrao || ""),
        brasao_asset: String(row.brasao_asset || ""),
        data_extracao: dataExtracaoStr,
      };
    }
  } catch (_error) {}

  return null;
}

export async function getEntidades(
  portalSlug = "porciuncula_prefeitura",
): Promise<EntidadeItem[]> {
  try {
    const result = await sql<{ id: string; nome: string }>`
      select empresa_id as id, nome from seed_porciuncula_prefeitura_orgaos where portal_slug = ${portalSlug}
    `.execute(db);

    if (result.rows.length > 0) {
      return result.rows.map((row) => ({
        id: String(row.id),
        nome: String(row.nome || ""),
      }));
    }
  } catch (_error) {}

  return [];
}
