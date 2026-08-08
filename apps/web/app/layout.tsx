import { getEntidades, getPortalConfig } from "@transparencia/db";
import { Ribbon } from "@transparencia/ui";
import { Analytics } from "@vercel/analytics/next";
import { SpeedInsights } from "@vercel/speed-insights/next";
import type { Metadata } from "next";
import { IBM_Plex_Sans, Source_Serif_4 } from "next/font/google";
import { NuqsAdapter } from "nuqs/adapters/next/app";
import { Suspense } from "react";
import { formatBaseUrl } from "@/lib/metadata";
import {
  generateDataCatalogSchema,
  generateGovernmentOrganizationSchema,
  JsonLd,
} from "../components/json-ld";
import { SidebarWrapper } from "./components/sidebar-wrapper";
import "./globals.css";

const defaultBaseUrl = formatBaseUrl(process.env.NEXT_PUBLIC_APP_URL);

export const metadata: Metadata = {
  metadataBase: new URL(defaultBaseUrl),
  title: {
    default: "TransparenciaWeb",
    template: "TransparenciaWeb - %s",
  },
  description:
    "Portal de Transparência Pública Municipal - Consulta de despesas, receitas, orçamentos, licitações, pessoal e previdência pública.",
  keywords: [
    "transparência pública",
    "portal de transparência",
    "contas públicas",
    "gestão fiscal",
    "município",
    "porciúncula",
  ],
  authors: [{ name: "TransparenciaWeb" }],
  creator: "TransparenciaWeb",
  publisher: "TransparenciaWeb",
  robots: {
    index: true,
    follow: true,
    googleBot: {
      index: true,
      follow: true,
      "max-video-preview": -1,
      "max-image-preview": "large",
      "max-snippet": -1,
    },
  },
  openGraph: {
    title: "TransparenciaWeb",
    description:
      "Portal de Transparência Pública Municipal - Consulta de despesas, receitas, orçamentos, licitações, pessoal e previdência pública.",
    url: defaultBaseUrl,
    siteName: "TransparenciaWeb",
    locale: "pt_BR",
    type: "website",
    images: [
      {
        url: `${defaultBaseUrl}/favicon.svg`,
        width: 1200,
        height: 630,
        alt: "TransparenciaWeb",
      },
    ],
  },
  twitter: {
    card: "summary_large_image",
    title: "TransparenciaWeb",
    description:
      "Portal de Transparência Pública Municipal - Consulta de despesas, receitas, orçamentos, licitações, pessoal e previdência pública.",
    images: [`${defaultBaseUrl}/favicon.svg`],
  },
  icons: {
    icon: [
      { url: "/favicon.svg", type: "image/svg+xml" },
      { url: "/favicon-32.png", sizes: "32x32", type: "image/png" },
    ],
    apple: [{ url: "/favicon-180.png", sizes: "180x180", type: "image/png" }],
  },
};

const ibmPlexSans = IBM_Plex_Sans({
  subsets: ["latin"],
  weight: ["400", "500", "600", "700"],
  variable: "--font-ibm-plex",
});

const sourceSerif4 = Source_Serif_4({
  subsets: ["latin"],
  weight: ["400", "600", "700"],
  variable: "--font-source-serif",
});

export default async function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  const portalConfig = await getPortalConfig();
  const entidades = await getEntidades();

  const governmentOrganizationSchema = generateGovernmentOrganizationSchema({
    displayName: portalConfig?.displayName,
    stateUF: portalConfig?.uf,
    officialPortalUrl: portalConfig?.portalUrl,
  });

  const dataCatalogSchema = generateDataCatalogSchema({
    displayName: portalConfig?.displayName,
    officialPortalUrl: portalConfig?.portalUrl,
  });

  return (
    <html
      lang="pt-BR"
      className={`${ibmPlexSans.variable} ${sourceSerif4.variable}`}
    >
      <head>
        <JsonLd schema={governmentOrganizationSchema} />
        <JsonLd schema={dataCatalogSchema} />
      </head>
      <body className="flex min-h-screen flex-col bg-canvas font-sans text-ink antialiased md:flex-row">
        <NuqsAdapter>
          <Suspense fallback={null}>
            <SidebarWrapper
              portalName={portalConfig?.displayName}
              stateUF={portalConfig?.uf}
              portalTitle={
                portalConfig
                  ? `Contas da ${portalConfig.displayName}`
                  : undefined
              }
              anoInicial={portalConfig?.anoInicial}
              lastExtractionDate={portalConfig?.dataExtracao}
              officialPortalUrl={portalConfig?.portalUrl}
              entidades={entidades}
            />
          </Suspense>
          <div className="flex min-w-0 flex-1 flex-col">
            <Ribbon portalName={portalConfig?.displayName} />
            <main className="mx-auto w-full max-w-[1000px] flex-1 overflow-x-hidden px-4 py-4 sm:px-6 md:px-10 md:py-8">
              {children}
            </main>
          </div>
        </NuqsAdapter>
        <Analytics />
        <SpeedInsights />
      </body>
    </html>
  );
}
