"use client";

import React from "react";
import Link from "next/link";
import { usePathname } from "next/navigation";
import { cn } from "../utils/cn";
import {
  LayoutDashboard,
  TrendingUp,
  PieChart,
  Receipt,
  FileText,
  Users,
  HeartPulse,
  Landmark,
  ExternalLink,
} from "lucide-react";

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
    <aside className="w-64 bg-white border-r border-borderLine flex flex-col justify-between h-screen sticky top-0 shrink-0 select-none">
      <div>
        {/* Header do Município */}
        <div className="p-5 border-b border-borderLine">
          <h1 className="font-serif font-bold text-lg text-ink leading-tight">
            Transparência Municipal
          </h1>
          <p className="text-xs text-subtleText mt-0.5">Porciúncula / RJ</p>
        </div>

        {/* Grupos de Navegação */}
        <nav className="p-4 space-y-6 overflow-y-auto">
          {NAV_GROUPS.map((group, gIdx) => (
            <div key={gIdx} className="space-y-1">
              <p className="px-3 text-[11px] font-semibold text-mutedText uppercase tracking-wider mb-2">
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
                      "flex items-center gap-2.5 px-3 py-2 rounded-lg text-xs font-medium transition-colors",
                      isActive
                        ? "bg-accent/10 text-accent font-semibold"
                        : "text-subtleText hover:bg-gray-50 hover:text-ink"
                    )}
                  >
                    <Icon className={cn("w-4 h-4 shrink-0", isActive ? "text-accent" : "text-mutedText")} />
                    <span>{item.name}</span>
                  </Link>
                );
              })}
            </div>
          ))}
        </nav>
      </div>

      {/* Footer com link para o portal oficial */}
      <div className="p-4 border-t border-borderLine bg-gray-50/50">
        <a
          href="http://servicos.porciuncula.rj.gov.br:8080/transparencia"
          target="_blank"
          rel="noopener noreferrer"
          className="flex items-center justify-between text-xs font-medium text-ink hover:text-accent transition-colors"
        >
          <span>Portal Oficial</span>
          <ExternalLink className="w-3.5 h-3.5 text-mutedText" />
        </a>
        <p className="text-[10px] text-mutedText mt-1">
          Dados extraídos e consolidados via ELT
        </p>
      </div>
    </aside>
  );
}
