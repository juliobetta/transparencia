import { getPortalSlugs } from "@transparencia/db";
import type { MetadataRoute } from "next";
import { formatBaseUrl } from "@/lib/metadata";

export default async function sitemap(): Promise<MetadataRoute.Sitemap> {
  const baseUrl = formatBaseUrl(process.env.NEXT_PUBLIC_APP_URL);
  const currentDate = new Date();

  const staticRoutes: MetadataRoute.Sitemap = [
    {
      url: `${baseUrl}`,
      lastModified: currentDate,
      changeFrequency: "daily",
      priority: 1.0,
    },
    {
      url: `${baseUrl}/llms.txt`,
      lastModified: currentDate,
      changeFrequency: "weekly",
      priority: 0.5,
    },
    {
      url: `${baseUrl}/llms-full.txt`,
      lastModified: currentDate,
      changeFrequency: "weekly",
      priority: 0.5,
    },
  ];

  const portalSlugs = await getPortalSlugs();
  const subRoutes = [
    { path: "", priority: 0.9, changeFrequency: "daily" as const },
    { path: "/despesas", priority: 0.8, changeFrequency: "daily" as const },
    { path: "/receitas", priority: 0.8, changeFrequency: "daily" as const },
    { path: "/orcamento", priority: 0.8, changeFrequency: "weekly" as const },
    { path: "/licitacoes", priority: 0.8, changeFrequency: "daily" as const },
    { path: "/pessoal", priority: 0.8, changeFrequency: "monthly" as const },
    { path: "/caprem", priority: 0.8, changeFrequency: "monthly" as const },
    { path: "/saude", priority: 0.8, changeFrequency: "weekly" as const },
  ];

  const dynamicRoutes: MetadataRoute.Sitemap = portalSlugs.flatMap((slug) => {
    return subRoutes.map((sub) => ({
      url: `${baseUrl}/${slug}${sub.path}`,
      lastModified: currentDate,
      changeFrequency: sub.changeFrequency,
      priority: sub.priority,
    }));
  });

  return [...staticRoutes, ...dynamicRoutes];
}
