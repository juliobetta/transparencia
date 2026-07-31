"use client";

import {
  ChevronDown,
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
import { useState } from "react";
import { cn } from "../utils/cn";
import { fmtDate } from "../utils/formatters";
import { MultiSelect, type MultiSelectOption } from "./multi-select";

export interface NavGroup {
  label: string;
  items: {
    name: string;
    href: string;
    icon: React.ComponentType<{
      className?: string;
      strokeWidth?: number | string;
    }>;
  }[];
}

const NAV_GROUPS: NavGroup[] = [
  {
    label: "Administrativo",
    items: [
      { name: "Receitas", href: "/receitas", icon: TrendingUp },
      { name: "Execução Orçamentária", href: "/orcamento", icon: PieChart },
      { name: "Despesas Detalhadas", href: "/despesas", icon: Receipt },
      { name: "Licitações e Contratos", href: "/licitacoes", icon: FileText },
      { name: "Pessoal", href: "/pessoal", icon: Users },
    ],
  },
  {
    label: "Temas",
    items: [
      { name: "Saúde", href: "/saude", icon: HeartPulse },
      { name: "CAPREM", href: "/caprem", icon: Landmark },
    ],
  },
];

export interface SidebarProps {
  portalName?: string;
  stateUF?: string;
  portalTitle?: string;
  anoInicial?: number;
  entidades?: MultiSelectOption[];
  lastExtractionDate?: string;
  officialPortalUrl?: string;
  brasaoAsset?: string;
  selectedExercice?: string;
  onExerciceChange?: (year: string) => void;
  selectedEntidades?: string[];
  onEntidadesChange?: (selectedIds: string[]) => void;
  portalSlug?: string;
}

function buildNavUrl({
  path,
  slug,
  exercice,
  entidades,
}: {
  path: string;
  slug: string;
  exercice?: string;
  entidades?: string[];
}): string {
  const slugPrefix = slug ? `/${slug}` : "";
  const basePath = path === "/" ? slugPrefix || "/" : `${slugPrefix}${path}`;

  const params = new URLSearchParams();
  if (exercice) {
    params.set("ano", exercice);
  }
  if (entidades && entidades.length > 0) {
    params.set("entidades", entidades.join(","));
  }
  const queryString = params.toString();
  return queryString ? `${basePath}?${queryString}` : basePath;
}

export function Sidebar({
  portalName,
  stateUF,
  portalTitle,
  anoInicial,
  entidades = [],
  lastExtractionDate,
  officialPortalUrl,
  brasaoAsset,
  selectedExercice,
  onExerciceChange,
  selectedEntidades,
  onEntidadesChange,
  portalSlug = "porciuncula_prefeitura",
}: SidebarProps) {
  const pathname = usePathname();
  const currentYear = new Date().getFullYear();
  const [internalExercice, setInternalExercice] = useState(String(currentYear));
  const [internalEntidades, setInternalEntidades] = useState<string[]>([]);
  const [imgError, setImgError] = useState(false);

  const currentExercice = selectedExercice ?? internalExercice;
  const handleExerciceChange = (val: string) => {
    setInternalExercice(val);
    onExerciceChange?.(val);
  };

  const currentEntidades = selectedEntidades ?? internalEntidades;
  const handleEntidadesChange = (ids: string[]) => {
    setInternalEntidades(ids);
    onEntidadesChange?.(ids);
  };

  const displayTitle = portalTitle || `Contas da ${portalName}`;

  // Gerar anos dinâmicos do ano atual até anoInicial
  const maxYear = currentYear;
  const minYear = anoInicial ?? 2021;
  const years = Array.from(
    { length: Math.max(1, maxYear - minYear + 1) },
    (_, i) => String(maxYear - i),
  );

  const normalizedBrasao = brasaoAsset
    ? brasaoAsset.startsWith("/")
      ? brasaoAsset
      : `/${brasaoAsset}`
    : "/brasao-porciuncula.svg";

  const displayExtractionDate = fmtDate(lastExtractionDate);

  const visaoGeralHref = buildNavUrl({
    path: "/",
    slug: portalSlug,
    exercice: currentExercice,
    entidades: currentEntidades,
  });
  const isVisaoGeralActive =
    pathname === "/" ||
    pathname === `/${portalSlug}` ||
    pathname === `/${portalSlug}/`;

  return (
    <aside className="sticky top-0 flex h-screen w-[266px] shrink-0 select-none flex-col justify-between border-borderLine border-r bg-white">
      <div className="flex flex-col overflow-y-auto">
        {/* Marca Superior / Brasão Municipal */}
        <div className="border-borderLine border-b p-4">
          <div className="flex items-center gap-3">
            <div className="flex h-10 w-10 shrink-0 items-center justify-center overflow-hidden rounded-lg border border-borderLine bg-gray-50 p-1 shadow-sm">
              {!imgError && normalizedBrasao ? (
                /* biome-ignore lint/performance/noImgElement: brasao asset */
                <img
                  src={normalizedBrasao}
                  alt={`Brasão de ${portalName}`}
                  className="h-full w-full object-contain"
                  onError={() => setImgError(true)}
                />
              ) : (
                <Landmark
                  strokeWidth={1.6}
                  className="h-5 w-5 text-subtleText"
                />
              )}
            </div>
            <div>
              <h1 className="font-bold font-serif text-base text-ink leading-tight">
                {displayTitle}
              </h1>
              <p className="text-[11px] text-mutedText">
                Orçamento municipal · {stateUF}
              </p>
            </div>
          </div>
        </div>

        {/* Seção de Filtros */}
        <div className="space-y-2.5 border-borderLine border-b bg-gray-50/50 px-4 py-3.5">
          <p className="font-semibold text-[11px] text-mutedText">Filtros</p>
          <div className="space-y-2">
            <div>
              <label
                htmlFor="exercice-select"
                className="mb-1 block font-medium text-[11px] text-subtleText"
              >
                Exercício
              </label>
              <div className="relative w-full">
                <select
                  id="exercice-select"
                  value={currentExercice}
                  onChange={(e) => handleExerciceChange(e.target.value)}
                  className="w-full cursor-pointer appearance-none rounded-md border border-borderLine bg-white px-2.5 py-1.5 pr-8 font-medium text-ink text-xs shadow-sm transition-colors hover:border-gray-400 focus:border-[#1d64d8] focus:outline-none"
                >
                  {years.map((yr) => (
                    <option key={yr} value={yr}>
                      {yr}
                    </option>
                  ))}
                </select>
                <ChevronDown
                  strokeWidth={1.6}
                  className="pointer-events-none absolute top-1/2 right-2.5 h-3.5 w-3.5 -translate-y-1/2 text-mutedText"
                />
              </div>
            </div>
            <div>
              <span className="mb-1 block font-medium text-[11px] text-subtleText">
                Entidade
              </span>
              <MultiSelect
                options={entidades}
                selectedIds={currentEntidades}
                onChange={handleEntidadesChange}
              />
            </div>
          </div>
        </div>

        {/* Navegação Principal */}
        <nav className="space-y-4 p-4">
          {/* Opção "Visão geral" isolada no topo sem cabeçalho de grupo */}
          <div>
            <Link
              href={visaoGeralHref}
              className={cn(
                "flex items-center gap-2.5 rounded-lg px-3 py-2 font-medium text-xs transition-colors",
                isVisaoGeralActive
                  ? "bg-[oklch(0.55_0.11_250)]/10 font-semibold text-[oklch(0.55_0.11_250)]"
                  : "text-subtleText hover:bg-gray-50 hover:text-ink",
              )}
            >
              <LayoutDashboard
                strokeWidth={1.6}
                className={cn(
                  "h-4 w-4 shrink-0",
                  isVisaoGeralActive
                    ? "text-[oklch(0.55_0.11_250)]"
                    : "text-mutedText",
                )}
              />
              <span>Visão geral</span>
            </Link>
          </div>

          {/* Demais Grupos de Navegação */}
          {NAV_GROUPS.map((group) => (
            <div key={group.label} className="space-y-1">
              <p className="mb-1.5 px-3 font-semibold text-[11px] text-mutedText">
                {group.label}
              </p>
              {group.items.map((item) => {
                const targetPath = portalSlug
                  ? `/${portalSlug}${item.href}`
                  : item.href;
                const isActive =
                  pathname === item.href ||
                  pathname === targetPath ||
                  (pathname
                    ? pathname.startsWith(targetPath) ||
                      pathname.startsWith(item.href)
                    : false);
                const itemHref = buildNavUrl({
                  path: item.href,
                  slug: portalSlug,
                  exercice: currentExercice,
                  entidades: currentEntidades,
                });
                const Icon = item.icon;
                return (
                  <Link
                    key={item.href}
                    href={itemHref}
                    className={cn(
                      "flex items-center gap-2.5 rounded-lg px-3 py-2 font-medium text-xs transition-colors",
                      isActive
                        ? "bg-[oklch(0.55_0.11_250)]/10 font-semibold text-[oklch(0.55_0.11_250)]"
                        : "text-subtleText hover:bg-gray-50 hover:text-ink",
                    )}
                  >
                    <Icon
                      strokeWidth={1.6}
                      className={cn(
                        "h-4 w-4 shrink-0",
                        isActive
                          ? "text-[oklch(0.55_0.11_250)]"
                          : "text-mutedText",
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

      {/* Rodapé com Data de Extração Dinâmica */}
      <div className="space-y-1.5 border-borderLine border-t bg-gray-50/50 p-4">
        {officialPortalUrl && (
          <a
            href={officialPortalUrl}
            target="_blank"
            rel="noopener noreferrer"
            className="flex items-center justify-between font-medium text-ink text-xs transition-colors hover:text-[#1d64d8]"
          >
            <span>Portal oficial</span>
            <ExternalLink
              strokeWidth={1.6}
              className="h-3.5 w-3.5 text-mutedText"
            />
          </a>
        )}
        <div className="space-y-0.5 text-[10px] text-mutedText">
          <p>Dados extraídos do Portal Oficial</p>
          <p className="font-mono text-[9.5px]">
            Última extração: {displayExtractionDate}
          </p>
        </div>
      </div>
    </aside>
  );
}
