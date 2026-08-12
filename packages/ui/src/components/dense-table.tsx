"use client";

import {
  ChevronDown,
  ChevronsUpDown,
  ChevronUp,
  Download,
  Search,
} from "lucide-react";
import { useMemo, useState } from "react";
import { cn } from "../utils/cn";
import {
  fmtCompact,
  fmtCurrency,
  fmtDate,
  fmtNumber,
  fmtPercent,
} from "../utils/formatters";
import { Badge } from "./badge";

export interface Column<T> {
  header: string;
  accessorKey?: keyof T;
  align?: "left" | "center" | "right";
  isSerifNumeric?: boolean;
  format?:
    | "currency"
    | "percent"
    | "number"
    | "compact"
    | "statusBadge"
    | "caspBadge"
    | "date";
  className?: string;
  sortable?: boolean;
  renderCell?: (row: T) => React.ReactNode;
}

export interface DenseTableProps<T> {
  data: T[];
  columns: Column<T>[];
  searchPlaceholder?: string;
  searchableKeys?: (keyof T)[];
  pageSize?: number;
  emptyMessage?: string;
  className?: string;
  rowKey?: keyof T;
  sortable?: boolean;
  enableExportCsv?: boolean;
  exportFilename?: string;
}

// biome-ignore lint/suspicious/noExplicitAny: T accepts any typed object model
export function DenseTable<T extends Record<string, any>>({
  data,
  columns,
  searchPlaceholder = "Buscar...",
  searchableKeys,
  pageSize,
  emptyMessage = "Nenhum registro encontrado.",
  className,
  rowKey,
  sortable = false,
  enableExportCsv = true,
  exportFilename = "lancamentos.csv",
}: DenseTableProps<T>) {
  const [query, setQuery] = useState("");
  const [page, setPage] = useState(1);
  const [sortKey, setSortKey] = useState<keyof T | null>(null);
  const [sortDir, setSortDir] = useState<"asc" | "desc">("asc");

  const filteredData = useMemo(() => {
    if (!query.trim()) return data;
    const q = query.toLowerCase();
    return data.filter((row) => {
      const keysToSearch = searchableKeys || (Object.keys(row) as (keyof T)[]);
      return keysToSearch.some((k) => {
        const val = row[k];
        return (
          val !== null &&
          val !== undefined &&
          String(val).toLowerCase().includes(q)
        );
      });
    });
  }, [data, query, searchableKeys]);

  const handleSort = (key?: keyof T) => {
    if (!key) return;
    if (sortKey === key) {
      if (sortDir === "asc") {
        setSortDir("desc");
      } else {
        setSortKey(null);
        setSortDir("asc");
      }
    } else {
      setSortKey(key);
      setSortDir("asc");
    }
  };

  const sortedData = useMemo(() => {
    if (!sortKey) return filteredData;
    return [...filteredData].sort((a, b) => {
      const valA = a[sortKey];
      const valB = b[sortKey];
      if (valA === valB) return 0;
      if (valA === null || valA === undefined) return 1;
      if (valB === null || valB === undefined) return -1;

      let cmp = 0;
      if (typeof valA === "number" && typeof valB === "number") {
        cmp = valA - valB;
      } else {
        cmp = String(valA).localeCompare(String(valB), "pt-BR", {
          numeric: true,
        });
      }
      return sortDir === "asc" ? cmp : -cmp;
    });
  }, [filteredData, sortKey, sortDir]);

  const totalPages = pageSize
    ? Math.max(1, Math.ceil(sortedData.length / pageSize))
    : 1;
  const currentPage = Math.min(page, totalPages);

  const displayedData = useMemo(() => {
    if (!pageSize) return sortedData;
    const start = (currentPage - 1) * pageSize;
    return sortedData.slice(start, start + pageSize);
  }, [sortedData, pageSize, currentPage]);

  const handleExportCsv = () => {
    if (!sortedData.length) return;
    const headerRow = columns
      .map((c) => `"${c.header.replace(/"/g, '""')}"`)
      .join(",");
    const bodyRows = sortedData.map((row) =>
      columns
        .map((col) => {
          const val = col.accessorKey ? row[col.accessorKey] : "";
          const strVal = val === null || val === undefined ? "" : String(val);
          return `"${strVal.replace(/"/g, '""')}"`;
        })
        .join(","),
    );
    const csvContent = `\uFEFF${[headerRow, ...bodyRows].join("\r\n")}`;
    const blob = new Blob([csvContent], { type: "text/csv;charset=utf-8;" });
    const url = URL.createObjectURL(blob);
    const link = document.createElement("a");
    link.href = url;
    link.setAttribute("download", exportFilename);
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
    URL.revokeObjectURL(url);
  };

  const getRowId = (row: T, idx: number): string => {
    if (rowKey && row[rowKey] !== undefined && row[rowKey] !== null) {
      return String(row[rowKey]);
    }
    const firstColKey = columns[0]?.accessorKey
      ? String(row[columns[0].accessorKey] ?? "")
      : "";
    return firstColKey ? `${firstColKey}-${idx}` : `row-${idx}`;
  };

  const renderCellValue = (col: Column<T>, row: T) => {
    if (col.renderCell) {
      return col.renderCell(row);
    }
    const raw = col.accessorKey ? row[col.accessorKey] : undefined;
    if (raw === null || raw === undefined) return "-";

    if (col.format === "date") {
      return fmtDate(String(raw));
    }
    if (col.format === "currency") {
      const num =
        typeof raw === "number"
          ? raw
          : parseFloat(String(raw).replace(",", ".")) || 0;
      return fmtCurrency(num);
    }
    if (col.format === "compact") {
      const num =
        typeof raw === "number"
          ? raw
          : parseFloat(String(raw).replace(",", ".")) || 0;
      return fmtCompact(num);
    }
    if (col.format === "percent") {
      const num = typeof raw === "number" ? raw : parseFloat(String(raw)) || 0;
      return fmtPercent(num);
    }
    if (col.format === "number") {
      const num = typeof raw === "number" ? raw : parseFloat(String(raw)) || 0;
      return fmtNumber(num);
    }
    if (col.format === "statusBadge" || col.format === "caspBadge") {
      const valStr = String(raw);
      const variant =
        (row.alertaBadgeVariant as
          | "warning"
          | "accent"
          | "default"
          | "success"
          | "danger") ||
        (valStr.includes("Atenção") ||
        valStr === "excesso" ||
        valStr === "Acima do Limite"
          ? "warning"
          : valStr.includes("Conformidade") || valStr.includes("Clínica")
            ? "success"
            : valStr.includes("Consórcio")
              ? "accent"
              : "default");
      return <Badge variant={variant}>{valStr}</Badge>;
    }

    return String(raw);
  };

  const pageNumbers = useMemo(() => {
    if (totalPages <= 7) {
      return Array.from({ length: totalPages }, (_, i) => i + 1);
    }
    const pages: (number | string)[] = [];
    pages.push(1);
    if (currentPage > 3) {
      pages.push("ellipsis-start");
    }
    const start = Math.max(2, currentPage - 1);
    const end = Math.min(totalPages - 1, currentPage + 1);
    for (let i = start; i <= end; i++) {
      pages.push(i);
    }
    if (currentPage < totalPages - 2) {
      pages.push("ellipsis-end");
    }
    pages.push(totalPages);
    return pages;
  }, [totalPages, currentPage]);

  return (
    <div
      className={cn(
        "overflow-hidden rounded-xl border border-borderLine bg-white shadow-xs",
        className,
      )}
    >
      {(searchableKeys !== undefined || enableExportCsv) && (
        <div className="flex flex-col gap-2 border-borderLine border-b bg-gray-50/50 p-3 sm:flex-row sm:items-center sm:justify-between">
          {searchableKeys !== undefined ? (
            <div className="flex flex-1 items-center gap-2">
              <Search className="h-4 w-4 shrink-0 text-mutedText" />
              <input
                type="text"
                value={query}
                onChange={(e) => {
                  setQuery(e.target.value);
                  setPage(1);
                }}
                placeholder={searchPlaceholder}
                className="w-full bg-transparent text-ink text-xs placeholder:text-mutedText focus:outline-none"
              />
            </div>
          ) : (
            <div />
          )}

          {enableExportCsv && (
            <button
              type="button"
              onClick={handleExportCsv}
              disabled={sortedData.length === 0}
              className="inline-flex min-h-[44px] shrink-0 items-center justify-center gap-1.5 rounded-lg border border-slate-200 bg-white px-3 py-2.5 font-medium text-slate-700 text-xs transition-colors hover:border-slate-300 hover:bg-slate-50 disabled:opacity-40 sm:min-h-0 sm:py-1.5"
            >
              <Download className="h-3.5 w-3.5 text-slate-500" />
              Baixar CSV
            </button>
          )}
        </div>
      )}
      <div className="overflow-x-auto">
        <table className="w-full border-collapse text-left text-xs">
          <thead>
            <tr className="border-borderLine border-b bg-gray-100/70 font-semibold text-subtleText uppercase tracking-wider">
              {columns.map((col, _idx) => {
                const isSortable =
                  (col.sortable ?? sortable) && col.accessorKey !== undefined;
                const isSorted = sortKey === col.accessorKey;
                return (
                  <th
                    key={col.header}
                    scope="col"
                    onClick={() => isSortable && handleSort(col.accessorKey)}
                    className={cn(
                      "select-none px-3 py-2.5 sm:px-4",
                      isSortable &&
                        "cursor-pointer transition-colors hover:bg-gray-200/60",
                      col.align === "right" && "text-right",
                      col.align === "center" && "text-center",
                      col.className,
                    )}
                  >
                    <div
                      className={cn(
                        "inline-flex items-center gap-1.5",
                        col.align === "right" && "justify-end",
                        col.align === "center" && "justify-center",
                      )}
                    >
                      <span>{col.header}</span>
                      {isSortable && (
                        <span className="inline-flex shrink-0 items-center text-slate-400">
                          {isSorted ? (
                            sortDir === "asc" ? (
                              <ChevronUp className="h-3.5 w-3.5 text-[#2b6cb0]" />
                            ) : (
                              <ChevronDown className="h-3.5 w-3.5 text-[#2b6cb0]" />
                            )
                          ) : (
                            <ChevronsUpDown className="h-3.5 w-3.5 opacity-35 hover:opacity-100" />
                          )}
                        </span>
                      )}
                    </div>
                  </th>
                );
              })}
            </tr>
          </thead>
          <tbody className="divide-y divide-gray-100">
            {displayedData.length === 0 ? (
              <tr>
                <td
                  colSpan={columns.length}
                  className="px-4 py-6 text-center text-mutedText italic"
                >
                  {emptyMessage}
                </td>
              </tr>
            ) : (
              displayedData.map((row, index) => {
                const rKey = getRowId(row, index);
                return (
                  <tr
                    key={`tr-${rKey}`}
                    className="transition-colors hover:bg-gray-50/80"
                  >
                    {columns.map((col) => (
                      <td
                        key={`td-${rKey}-${String(col.accessorKey || col.header)}`}
                        title={
                          col.accessorKey &&
                          row[col.accessorKey] !== null &&
                          row[col.accessorKey] !== undefined
                            ? String(row[col.accessorKey])
                            : undefined
                        }
                        className={cn(
                          col.className ? col.className : "whitespace-nowrap",
                          "px-3 py-2 text-ink sm:px-4",
                          col.align === "right" && "text-right",
                          col.align === "center" && "text-center",
                          (col.isSerifNumeric ||
                            col.format === "currency" ||
                            col.format === "compact") &&
                            "font-semibold font-serif",
                          row.className,
                        )}
                      >
                        {renderCellValue(col, row)}
                      </td>
                    ))}
                  </tr>
                );
              })
            )}
          </tbody>
        </table>
      </div>

      {pageSize && (
        <div className="flex flex-col items-center justify-between gap-3 border-slate-100 border-t bg-white px-4 py-3 text-slate-500 text-xs sm:flex-row sm:px-5">
          <div>
            Mostrando{" "}
            <span className="font-semibold text-slate-700">
              {displayedData.length}
            </span>{" "}
            de{" "}
            <span className="font-semibold text-slate-700">
              {filteredData.length}
            </span>{" "}
            registros
          </div>

          {totalPages > 1 && (
            <div className="flex flex-wrap items-center gap-1.5">
              <button
                type="button"
                disabled={currentPage <= 1}
                onClick={() => setPage((p) => Math.max(1, p - 1))}
                className="flex h-9 w-9 items-center justify-center rounded-lg border border-slate-200 bg-white text-slate-600 transition-colors hover:bg-slate-50 disabled:cursor-not-allowed disabled:opacity-40 sm:h-7 sm:w-7"
              >
                &larr;
              </button>

              {pageNumbers.map((pageNum) =>
                typeof pageNum === "string" ? (
                  <span
                    key={pageNum}
                    className="px-1 font-semibold text-slate-400"
                  >
                    ...
                  </span>
                ) : (
                  <button
                    key={`page-btn-${pageNum}`}
                    type="button"
                    onClick={() => setPage(pageNum)}
                    className={cn(
                      "flex h-9 w-9 items-center justify-center rounded-lg font-semibold text-xs transition-colors sm:h-7 sm:w-7",
                      pageNum === currentPage
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
                disabled={currentPage >= totalPages}
                onClick={() => setPage((p) => Math.min(totalPages, p + 1))}
                className="flex h-9 w-9 items-center justify-center rounded-lg border border-slate-200 bg-white text-slate-600 transition-colors hover:bg-slate-50 disabled:cursor-not-allowed disabled:opacity-40 sm:h-7 sm:w-7"
              >
                &rarr;
              </button>
            </div>
          )}
        </div>
      )}
    </div>
  );
}
