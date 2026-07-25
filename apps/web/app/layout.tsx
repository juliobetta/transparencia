import { Sidebar } from "@transparencia/ui";
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

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html
      lang="pt-BR"
      className={`${ibmPlexSans.variable} ${sourceSerif4.variable}`}
    >
      <body className="flex min-h-screen bg-canvas text-ink antialiased">
        <Sidebar />
        <div className="max-w-7xl flex-1 overflow-x-hidden p-8">{children}</div>
      </body>
    </html>
  );
}
