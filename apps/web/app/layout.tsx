import { getEntidades, getPortalConfig } from "@transparencia/db";
import { Ribbon, Sidebar } from "@transparencia/ui";
import type { Metadata } from "next";
import { IBM_Plex_Sans, Source_Serif_4 } from "next/font/google";
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

export const metadata: Metadata = {
  title: "Portal de Transparência — Porciúncula/RJ",
  description:
    "Portal Cívico de Transparência Fiscal e Orçamentária de Porciúncula",
};

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
        <Sidebar
          cityName={portalConfig?.display_name}
          stateUF={portalConfig?.uf}
          portalTitle={
            portalConfig ? `Contas de ${portalConfig.display_name}` : undefined
          }
          anoInicial={portalConfig?.ano_inicial}
          lastExtractionDate={portalConfig?.data_extracao}
          officialPortalUrl={portalConfig?.portal_url}
          entidades={entidades}
        />
        <div className="flex min-w-0 flex-1 flex-col">
          <Ribbon />
          <main className="max-w-7xl flex-1 overflow-x-hidden p-8">
            {children}
          </main>
        </div>
      </body>
    </html>
  );
}
