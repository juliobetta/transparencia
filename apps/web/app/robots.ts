import type { MetadataRoute } from "next";
import { formatBaseUrl } from "@/lib/metadata";

export default function robots(): MetadataRoute.Robots {
  const baseUrl = formatBaseUrl(process.env.NEXT_PUBLIC_APP_URL);

  return {
    rules: {
      userAgent: "*",
      allow: "/",
      disallow: ["/api/"],
    },
    sitemap: `${baseUrl}/sitemap.xml`,
  };
}
