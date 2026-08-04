"use client";

import { cn, fmtCurrency } from "@transparencia/ui";
import { ChevronDown, Download, Search } from "lucide-react";
import { useMemo, useState } from "react";

export interface ContratoSemLicitacaoItem {
  ano: number;
  empresa: string;
  numero: string;
  fornecedor: string;
  objeto: string;
  valorContrato: string | number;
  licitacaoNumero?: string;
  mes: number;
  numeroObra?: string | null;
  tipoObra?: string | null;
  modalidade?: string | null;
  fundlegal?: string | null;
  limiteDispensa?: number;
  acimaLimite?: boolean;
  periodo: string;
}

export interface LicitacoesTableProps {
  data: ContratoSemLicitacaoItem[];
  fracionamentoVendors?: Record<string, number>;
  pageSize?: number;
  className?: string;
}

export function LicitacoesTable({
  data,
  fracionamentoVendors = {},
  pageSize = 6,
  className,
}: LicitacoesTableProps) {
  const [query, setQuery] = useState("");
  const [sortBy, setSortBy] = useState<
    "maior_valor" | "menor_valor" | "fornecedor" | "periodo"
  >("maior_valor");
  const [currentPage, setCurrentPage] = useState(1);

  // Search & Filter
  const filteredData = useMemo(() => {
    let result = [...data];
    if (query.trim()) {
      const q = query.toLowerCase();
      result = result.filter(
        (row) =>
          row.fornecedor?.toLowerCase().includes(q) ||
          row.objeto?.toLowerCase().includes(q) ||
          row.modalidade?.toLowerCase().includes(q) ||
          row.numero?.toLowerCase().includes(q),
      );
    }

    // Sort
    result.sort((a, b) => {
      const valA =
        typeof a.valorContrato === "number"
          ? a.valorContrato
          : parseFloat(String(a.valorContrato ?? "0").replace(",", ".")) || 0;
      const valB =
        typeof b.valorContrato === "number"
          ? b.valorContrato
          : parseFloat(String(b.valorContrato ?? "0").replace(",", ".")) || 0;

      if (sortBy === "maior_valor") return valB - valA;
      if (sortBy === "menor_valor") return valA - valB;
      if (sortBy === "fornecedor")
        return (a.fornecedor || "").localeCompare(b.fornecedor || "");
      if (sortBy === "periodo") {
        return (b.mes || 0) - (a.mes || 0);
      }
      return 0;
    });

    return result;
  }, [data, query, sortBy]);

  // Pagination calculation
  const totalPages = Math.max(1, Math.ceil(filteredData.length / pageSize));
  const activePage = Math.min(currentPage, totalPages);
  const startIndex = (activePage - 1) * pageSize;
  const pageData = filteredData.slice(startIndex, startIndex + pageSize);

  // CSV Export
  const handleExportCSV = () => {
    if (filteredData.length === 0) return;
    const headers = [
      "FORNECEDOR",
      "OBJETO",
      "MODALIDADE",
      "VALOR (R$)",
      "PERIODO",
    ];
    const rows = filteredData.map((row) => {
      const val =
        typeof row.valorContrato === "number"
          ? row.valorContrato
          : parseFloat(String(row.valorContrato ?? "0").replace(",", ".")) || 0;
      return [
        `"${(row.fornecedor || "").replace(/"/g, '""')}"`,
        `"${(row.objeto || "").replace(/"/g, '""')}"`,
        `"${(row.modalidade || "Dispensa").replace(/"/g, '""')}"`,
        val.toFixed(2),
        `"${row.periodo || ""}"`,
      ];
    });

    const csvContent =
      "data:text/csv;charset=utf-8," +
      [headers.join(","), ...rows.map((r) => r.join(","))].join("\n");
    const encodedUri = encodeURI(csvContent);
    const link = document.createElement("a");
    link.setAttribute("href", encodedUri);
    link.setAttribute("download", "contratos_sem_licitacao.csv");
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
  };

  const getModalidadeBadgeVariant = (modalidadeStr?: string | null) => {
    const mod = (modalidadeStr || "Dispensa").toLowerCase();
    if (mod.includes("inexigibilidade")) {
      return "bg-[#edf2f7] text-[#2b6cb0] border-[#cbd5e0]";
    }
    if (mod.includes("dispensa")) {
      return "bg-[#fffaf0] text-[#9c4221] border-[#feebc8]";
    }
    if (mod.includes("pregã") || mod.includes("pregao")) {
      return "bg-[#ebf8ff] text-[#2c5282] border-[#bee3f8]";
    }
    return "bg-slate-100 text-slate-700 border-slate-200";
  };

  return (
    <div
      className={cn(
        "overflow-hidden rounded-2xl border border-slate-200/80 bg-white shadow-xs",
        className,
      )}
    >
      {/* Toolbar */}
      <div className="flex flex-col items-center justify-between gap-3 border-slate-100 border-b bg-slate-50/40 p-4 sm:flex-row">
        {/* Search */}
        <div className="relative w-full sm:w-80">
          <Search className="absolute top-1/2 left-3 h-4 w-4 -translate-y-1/2 text-slate-400" />
          <input
            type="text"
            value={query}
            onChange={(e) => {
              setQuery(e.target.value);
              setCurrentPage(1);
            }}
            placeholder="Buscar fornecedor, objeto ou modalidade..."
            className="w-full rounded-xl border border-slate-200 bg-white py-2 pr-3 pl-9 text-slate-800 text-xs shadow-2xs transition-all placeholder:text-slate-400 focus:border-slate-400 focus:outline-none"
          />
        </div>

        {/* Tools (Sort + CSV) */}
        <div className="flex w-full items-center justify-end gap-2 sm:w-auto">
          <div className="flex items-center gap-1.5 font-medium text-subtleText text-xs">
            <span>Ordenar por</span>
            <div className="relative">
              <select
                value={sortBy}
                onChange={(e) =>
                  setSortBy(
                    e.target.value as
                      | "maior_valor"
                      | "menor_valor"
                      | "fornecedor"
                      | "periodo",
                  )
                }
                className="cursor-pointer appearance-none rounded-md border border-borderLine bg-white px-2.5 py-1.5 pr-8 font-medium text-ink text-xs shadow-sm transition-colors hover:border-gray-400 focus:border-[#1d64d8] focus:outline-none"
              >
                <option value="maior_valor">Maior valor</option>
                <option value="menor_valor">Menor valor</option>
                <option value="fornecedor">Fornecedor (A-Z)</option>
                <option value="periodo">Período</option>
              </select>
              <ChevronDown
                strokeWidth={1.6}
                className="pointer-events-none absolute top-1/2 right-2.5 h-3.5 w-3.5 -translate-y-1/2 text-mutedText"
              />
            </div>
          </div>

          <button
            type="button"
            onClick={handleExportCSV}
            className="inline-flex cursor-pointer items-center gap-1.5 rounded-lg border border-slate-200 bg-white px-3 py-1.5 font-semibold text-slate-700 text-xs shadow-2xs transition-colors hover:bg-slate-50 hover:text-slate-900"
          >
            <Download className="h-3.5 w-3.5 text-slate-500" />
            <span>CSV</span>
          </button>
        </div>
      </div>

      {/* Table */}
      <div className="overflow-x-auto">
        <table className="w-full border-collapse text-left text-xs">
          <thead>
            <tr className="border-slate-100 border-b bg-slate-50/80 font-bold text-[11px] text-slate-400 uppercase tracking-wider">
              <th className="px-5 py-3">FORNECEDOR</th>
              <th className="px-5 py-3">OBJETO</th>
              <th className="px-5 py-3 text-center">MODALIDADE</th>
              <th className="px-5 py-3 text-right">VALOR</th>
              <th className="px-5 py-3 text-right">PERÍODO</th>
            </tr>
          </thead>
          <tbody className="divide-y divide-slate-100">
            {pageData.length === 0 ? (
              <tr>
                <td
                  colSpan={5}
                  className="px-5 py-8 text-center text-slate-400 italic"
                >
                  Nenhum contrato encontrado.
                </td>
              </tr>
            ) : (
              pageData.map((row, idx) => {
                const valNum =
                  typeof row.valorContrato === "number"
                    ? row.valorContrato
                    : parseFloat(
                        String(row.valorContrato ?? "0").replace(",", "."),
                      ) || 0;

                const fracCount = fracionamentoVendors[row.fornecedor] || 0;

                return (
                  <tr
                    key={`contrato-row-${row.numero || idx}-${row.fornecedor}`}
                    className="transition-colors hover:bg-slate-50/60"
                  >
                    {/* Fornecedor */}
                    <td className="px-5 py-3.5 align-top">
                      <div className="font-bold text-slate-900 leading-snug">
                        {row.fornecedor}
                      </div>
                      {fracCount >= 3 && (
                        <div className="mt-1 inline-flex items-center gap-1 rounded border border-[#feebc8] bg-[#fffaf0] px-2 py-0.5 font-medium text-[#9c4221] text-[11px]">
                          <span>⚠️</span> {fracCount} contratos próximos ao teto
                        </div>
                      )}
                    </td>

                    {/* Objeto */}
                    <td className="max-w-xs px-5 py-3.5 align-top text-slate-600 leading-normal">
                      {row.objeto}
                    </td>

                    {/* Modalidade */}
                    <td className="px-5 py-3.5 text-center align-top">
                      <span
                        className={cn(
                          "inline-block rounded-md border px-2.5 py-0.5 font-semibold text-[11px]",
                          getModalidadeBadgeVariant(row.modalidade),
                        )}
                      >
                        {row.modalidade || "Dispensa"}
                      </span>
                    </td>

                    {/* Valor */}
                    <td className="whitespace-nowrap px-5 py-3.5 text-right align-top font-bold font-serif text-slate-900 text-sm">
                      {fmtCurrency(valNum)}
                    </td>

                    {/* Período */}
                    <td className="whitespace-nowrap px-5 py-3.5 text-right align-top text-slate-500">
                      {row.periodo}
                    </td>
                  </tr>
                );
              })
            )}
          </tbody>
        </table>
      </div>

      {/* Pagination Footer */}
      <div className="flex flex-col items-center justify-between gap-3 border-slate-100 border-t bg-white px-5 py-3 text-slate-500 text-xs sm:flex-row">
        <div>
          Mostrando{" "}
          <span className="font-semibold text-slate-700">
            {pageData.length}
          </span>{" "}
          de{" "}
          <span className="font-semibold text-slate-700">
            {filteredData.length}
          </span>{" "}
          contratos
        </div>

        {totalPages > 1 && (
          <div className="flex items-center gap-1.5">
            <button
              type="button"
              disabled={activePage <= 1}
              onClick={() => setCurrentPage((p) => Math.max(1, p - 1))}
              className="flex h-7 w-7 items-center justify-center rounded-lg border border-slate-200 bg-white text-slate-600 transition-colors hover:bg-slate-50 disabled:cursor-not-allowed disabled:opacity-40"
            >
              &larr;
            </button>

            {Array.from({ length: totalPages }, (_, i) => i + 1).map(
              (pageNum) => (
                <button
                  key={`page-btn-${pageNum}`}
                  type="button"
                  onClick={() => setCurrentPage(pageNum)}
                  className={cn(
                    "flex h-7 w-7 items-center justify-center rounded-lg font-semibold text-xs transition-colors",
                    pageNum === activePage
                      ? "bg-[#2b6cb0] text-white"
                      : "border border-slate-200 bg-white text-slate-700 hover:bg-slate-50",
                  )}
                >
                  {pageNum}
                </button>
              ),
            )}

            <button
              type="button"
              disabled={activePage >= totalPages}
              onClick={() => setCurrentPage((p) => Math.min(totalPages, p + 1))}
              className="flex h-7 w-7 items-center justify-center rounded-lg border border-slate-200 bg-white text-slate-600 transition-colors hover:bg-slate-50 disabled:cursor-not-allowed disabled:opacity-40"
            >
              &rarr;
            </button>
          </div>
        )}
      </div>
    </div>
  );
}
