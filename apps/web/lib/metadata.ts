import { getPortalConfig } from "@transparencia/db";
import type { Metadata } from "next";
import { cache } from "react";

export const getCachedPortalConfig = cache(async (portalSlug: string) => {
  return getPortalConfig(portalSlug);
});

export async function createPortalMetadata(
  pageTitle: string,
  portalSlug: string,
): Promise<Metadata> {
  const portalConfig = await getCachedPortalConfig(portalSlug);
  const portalDisplayName =
    portalConfig?.displayName?.trim() || "Prefeitura de Porciúncula";

  return {
    title: `${pageTitle} | ${portalDisplayName}`,
  };
}
