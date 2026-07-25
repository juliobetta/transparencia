import type { Metadata } from "next";
import { IBM_Plex_Sans, Source_Serif_4 } from "next/font/google";
import { Sidebar } from "@transparencia/ui";
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
  description: "Portal Cívico de Transparência Fiscal e Orçamentária de Porciúncula",
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="pt-BR" className={`${ibmPlexSans.variable} ${sourceSerif4.variable}`}>
      <body className="bg-canvas text-ink antialiased flex min-h-screen">
        <Sidebar />
        <div className="flex-1 p-8 max-w-7xl overflow-x-hidden">{children}</div>
      </body>
    </html>
  );
}
