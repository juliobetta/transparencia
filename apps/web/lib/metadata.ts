import { getPortalConfig } from "@transparencia/db";
import type { Metadata } from "next";
import { cache } from "react";

export const getCachedPortalConfig = cache(async (portalSlug: string) => {
  return getPortalConfig(portalSlug);
});

export function formatBaseUrl(rawUrl?: string): string {
  const defaultUrl = "https://maistransparencia.com";
  const target = rawUrl?.trim() || defaultUrl;
  const formatted =
    target.startsWith("http://") || target.startsWith("https://")
      ? target
      : `https://${target}`;
  return formatted.replace(/\/+$/, "");
}

interface CreateMetadataOptions {
  description?: string;
  path?: string;
  keywords?: string[];
}

export async function createPortalMetadata(
  pageTitle: string,
  portalSlug: string,
  options?: CreateMetadataOptions,
): Promise<Metadata> {
  const portalConfig = await getCachedPortalConfig(portalSlug);
  const portalDisplayName =
    portalConfig?.displayName?.trim() || "Prefeitura de Porciúncula";
  const titleText = pageTitle?.trim() || "Visão Geral";
  const fullTitle = `${titleText} | ${portalDisplayName}`;
  const baseUrl = formatBaseUrl(process.env.NEXT_PUBLIC_APP_URL);
  const normPath = options?.path
    ? options.path.startsWith("/")
      ? options.path
      : `/${options.path}`
    : "";
  const pagePath = `/${portalSlug}${normPath}`;
  const canonicalUrl = `${baseUrl}${pagePath}`;
  const defaultDescription = `Dados de transparência pública municipal de ${portalDisplayName}. Consulta de ${titleText.toLowerCase()}, dados orçamentários e prestação de contas.`;
  const finalDescription = options?.description || defaultDescription;

  const defaultKeywords = [
    "transparência pública",
    "porciúncula",
    portalDisplayName,
    titleText.toLowerCase(),
    "contas públicas",
    "prestação de contas",
  ];
  const finalKeywords =
    options?.keywords && options.keywords.length > 0
      ? options.keywords
      : defaultKeywords;

  return {
    title: `${titleText} | ${portalDisplayName}`,
    description: finalDescription,
    keywords: finalKeywords,
    alternates: {
      canonical: canonicalUrl,
    },
    openGraph: {
      title: fullTitle,
      description: finalDescription,
      url: canonicalUrl,
      siteName: "MaisTransparencia",
      locale: "pt_BR",
      type: "website",
      images: [
        {
          url: `${baseUrl}/favicon.svg`,
          width: 1200,
          height: 630,
          alt: fullTitle,
        },
      ],
    },
    twitter: {
      card: "summary_large_image",
      title: fullTitle,
      description: finalDescription,
      images: [`${baseUrl}/favicon.svg`],
    },
  };
}
