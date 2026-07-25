import { getEntidades, getPortalConfig } from "@transparencia/db";
import { Ribbon } from "@transparencia/ui";
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
              portalName={portalConfig?.display_name}
              stateUF={portalConfig?.uf}
              portalTitle={
                portalConfig
                  ? `Contas da ${portalConfig.display_name}`
                  : undefined
              }
              anoInicial={portalConfig?.ano_inicial}
              lastExtractionDate={portalConfig?.data_extracao}
              officialPortalUrl={portalConfig?.portal_url}
              entidades={entidades}
            />
          </Suspense>
          <div className="flex min-w-0 flex-1 flex-col">
            <Ribbon portalName={portalConfig?.display_name} />
            <main className="mx-auto w-full max-w-[1000px] flex-1 overflow-x-hidden px-10 py-8">
              {children}
            </main>
          </div>
        </NuqsAdapter>
      </body>
    </html>
  );
}
