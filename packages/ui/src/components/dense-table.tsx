"use client";

import { Search } from "lucide-react";
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
}: DenseTableProps<T>) {
  const [query, setQuery] = useState("");
  const [page, setPage] = useState(1);

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

  const totalPages = pageSize
    ? Math.max(1, Math.ceil(filteredData.length / pageSize))
    : 1;
  const currentPage = Math.min(page, totalPages);

  const displayedData = useMemo(() => {
    if (!pageSize) return filteredData;
    const start = (currentPage - 1) * pageSize;
    return filteredData.slice(start, start + pageSize);
  }, [filteredData, pageSize, currentPage]);

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

  return (
    <div
      className={cn(
        "overflow-hidden rounded-xl border border-borderLine bg-white shadow-xs",
        className,
      )}
    >
      {searchableKeys !== undefined && (
        <div className="flex items-center gap-2 border-borderLine border-b bg-gray-50/50 p-3">
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
      )}
      <div className="overflow-x-auto">
        <table className="w-full border-collapse text-left text-xs">
          <thead>
            <tr className="border-borderLine border-b bg-gray-100/70 font-semibold text-subtleText uppercase tracking-wider">
              {columns.map((col, _idx) => (
                <th
                  key={col.header}
                  className={cn(
                    "px-4 py-2.5",
                    col.align === "right" && "text-right",
                    col.align === "center" && "text-center",
                    col.className,
                  )}
                >
                  {col.header}
                </th>
              ))}
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
                        className={cn(
                          col.className ? col.className : "whitespace-nowrap",
                          "px-4 py-2 text-ink",
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
        <div className="flex flex-col items-center justify-between gap-3 border-slate-100 border-t bg-white px-5 py-3 text-slate-500 text-xs sm:flex-row">
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
            <div className="flex items-center gap-1.5">
              <button
                type="button"
                disabled={currentPage <= 1}
                onClick={() => setPage((p) => Math.max(1, p - 1))}
                className="flex h-7 w-7 items-center justify-center rounded-lg border border-slate-200 bg-white text-slate-600 transition-colors hover:bg-slate-50 disabled:cursor-not-allowed disabled:opacity-40"
              >
                &larr;
              </button>

              {Array.from({ length: totalPages }, (_, i) => i + 1).map(
                (pageNum) => (
                  <button
                    key={`page-btn-${pageNum}`}
                    type="button"
                    onClick={() => setPage(pageNum)}
                    className={cn(
                      "flex h-7 w-7 items-center justify-center rounded-lg font-semibold text-xs transition-colors",
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
                className="flex h-7 w-7 items-center justify-center rounded-lg border border-slate-200 bg-white text-slate-600 transition-colors hover:bg-slate-50 disabled:cursor-not-allowed disabled:opacity-40"
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
