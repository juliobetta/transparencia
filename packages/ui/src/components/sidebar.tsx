"use client";

import {
  ExternalLink,
  FileText,
  HeartPulse,
  Landmark,
  LayoutDashboard,
  PieChart,
  Receipt,
  TrendingUp,
  Users,
} from "lucide-react";
import Link from "next/link";
import { usePathname } from "next/navigation";
import type React from "react";
import { cn } from "../utils/cn";

export interface NavGroup {
  label: string;
  items: {
    name: string;
    href: string;
    icon: React.ComponentType<{ className?: string }>;
  }[];
}

const NAV_GROUPS: NavGroup[] = [
  {
    label: "Visão Geral",
    items: [
      { name: "Visão Geral", href: "/", icon: LayoutDashboard },
      { name: "Receitas", href: "/receitas", icon: TrendingUp },
      { name: "Orçamento", href: "/orcamento", icon: PieChart },
      { name: "Despesas", href: "/despesas", icon: Receipt },
    ],
  },
  {
    label: "Administrativo",
    items: [
      { name: "Licitações & Contratos", href: "/licitacoes", icon: FileText },
      { name: "Pessoal", href: "/pessoal", icon: Users },
    ],
  },
  {
    label: "Temas Relevantes",
    items: [
      { name: "Saúde", href: "/saude", icon: HeartPulse },
      { name: "CAPREM", href: "/caprem", icon: Landmark },
    ],
  },
];

export function Sidebar() {
  const pathname = usePathname();

  return (
    <aside className="sticky top-0 flex h-screen w-64 shrink-0 select-none flex-col justify-between border-borderLine border-r bg-white">
      <div>
        {/* Header do Município */}
        <div className="border-borderLine border-b p-5">
          <h1 className="font-bold font-serif text-ink text-lg leading-tight">
            Transparência Municipal
          </h1>
          <p className="mt-0.5 text-subtleText text-xs">Porciúncula / RJ</p>
        </div>

        {/* Grupos de Navegação */}
        <nav className="space-y-6 overflow-y-auto p-4">
          {NAV_GROUPS.map((group, gIdx) => (
            <div key={gIdx} className="space-y-1">
              <p className="mb-2 px-3 font-semibold text-[11px] text-mutedText uppercase tracking-wider">
                {group.label}
              </p>
              {group.items.map((item) => {
                const isActive = pathname === item.href;
                const Icon = item.icon;
                return (
                  <Link
                    key={item.href}
                    href={item.href}
                    className={cn(
                      "flex items-center gap-2.5 rounded-lg px-3 py-2 font-medium text-xs transition-colors",
                      isActive
                        ? "bg-accent/10 font-semibold text-accent"
                        : "text-subtleText hover:bg-gray-50 hover:text-ink",
                    )}
                  >
                    <Icon
                      className={cn(
                        "h-4 w-4 shrink-0",
                        isActive ? "text-accent" : "text-mutedText",
                      )}
                    />
                    <span>{item.name}</span>
                  </Link>
                );
              })}
            </div>
          ))}
        </nav>
      </div>

      {/* Footer com link para o portal oficial */}
      <div className="border-borderLine border-t bg-gray-50/50 p-4">
        <a
          href="http://servicos.porciuncula.rj.gov.br:8080/transparencia"
          target="_blank"
          rel="noopener noreferrer"
          className="flex items-center justify-between font-medium text-ink text-xs transition-colors hover:text-accent"
        >
          <span>Portal Oficial</span>
          <ExternalLink className="h-3.5 w-3.5 text-mutedText" />
        </a>
        <p className="mt-1 text-[10px] text-mutedText">
          Dados extraídos e consolidados via ELT
        </p>
      </div>
    </aside>
  );
}
