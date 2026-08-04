import { getEntidades, getPortalConfig } from "@transparencia/db";
import { Ribbon } from "@transparencia/ui";
import { Analytics } from "@vercel/analytics/next";
import { SpeedInsights } from "@vercel/speed-insights/next";
import { IBM_Plex_Sans, Source_Serif_4 } from "next/font/google";
import { NuqsAdapter } from "nuqs/adapters/next/app";
import { Suspense } from "react";
import { SidebarWrapper } from "./components/sidebar-wrapper";
import "./globals.css";

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

  return (
    <html
      lang="pt-BR"
      className={`${ibmPlexSans.variable} ${sourceSerif4.variable}`}
    >
      <body className="flex min-h-screen bg-canvas font-sans text-ink antialiased">
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
            <main className="mx-auto w-full max-w-[1000px] flex-1 overflow-x-hidden px-10 py-8">
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
