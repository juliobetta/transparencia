import { sql } from "kysely";
import { db } from "../client";

export interface PortalConfig {
  portalSlug: string;
  displayName: string;
  uf: string;
  portalUrl: string;
  baseHost: string;
  cidadeClean: string;
  anoInicial: number;
  empresaPadrao: string;
  brasaoAsset: string;
  dataExtracao: string;
}

export interface EntidadeItem {
  id: string;
  nome: string;
}

export async function getPortalConfig(
  portalSlug = "porciuncula_prefeitura",
): Promise<PortalConfig | null> {
  try {
    const result = await sql<Record<string, unknown>>`
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
        portalSlug: String(row.portal_slug || ""),
        displayName: String(row.display_name || ""),
        uf: String(row.uf || ""),
        portalUrl: String(row.portal_url || ""),
        baseHost: String(row.base_host || ""),
        cidadeClean: String(row.cidade_clean || ""),
        anoInicial: Number(row.ano_inicial) || new Date().getFullYear(),
        empresaPadrao: String(row.empresa_padrao || ""),
        brasaoAsset: String(row.brasao_asset || ""),
        dataExtracao: dataExtracaoStr,
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
      select empresa_id as id, orgao_nome as nome from dim_orgao where portal_slug = ${portalSlug}
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

export async function getPortalSlugs(): Promise<string[]> {
  try {
    const result = await sql<{ portal_slug: string }>`
      select distinct portal_slug from dim_portais where portal_slug is not null
    `.execute(db);

    if (result.rows.length > 0) {
      return result.rows.map((row) => String(row.portal_slug)).filter(Boolean);
    }
  } catch (_error) {}

  return ["porciuncula_prefeitura"];
}
