import type { MetadataRoute } from "next";

export default function manifest(): MetadataRoute.Manifest {
  return {
    name: "MaisTransparencia",
    short_name: "MaisTransparencia",
    description:
      "Portal de Transparência Pública Municipal - Consulta de despesas, receitas, orçamentos, licitações, pessoal e previdência pública.",
    start_url: "/?mode=standalone",
    display: "standalone",
    background_color: "#0f172a",
    theme_color: "#1e3a8a",
    icons: [
      {
        src: "/favicon-192.png",
        sizes: "192x192",
        type: "image/png",
        purpose: "any",
      },
      {
        src: "/favicon-192.png",
        sizes: "192x192",
        type: "image/png",
        purpose: "maskable",
      },
      {
        src: "/favicon-512.png",
        sizes: "512x512",
        type: "image/png",
        purpose: "any",
      },
      {
        src: "/favicon-512.png",
        sizes: "512x512",
        type: "image/png",
        purpose: "maskable",
      },
    ],
    screenshots: [
      {
        src: "/screenshot-desktop.png",
        sizes: "1280x720",
        type: "image/png",
        form_factor: "wide",
        label: "Portal de Transparência Municipal no Desktop",
      },
      {
        src: "/screenshot-mobile.png",
        sizes: "390x844",
        type: "image/png",
        form_factor: "narrow",
        label: "Portal de Transparência Municipal no Mobile",
      },
    ],
  };
}
