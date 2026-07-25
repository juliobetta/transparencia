"use client";

import React, { useState, useMemo } from "react";
import { clsx } from "clsx";
import { Search } from "lucide-react";
import { fmtCurrency, fmtPercent, fmtNumber, fmtCompact } from "../utils/formatters";
import { Badge } from "./badge";

export interface Column<T> {
  header: string;
  accessorKey?: keyof T;
  align?: "left" | "center" | "right";
  isSerifNumeric?: boolean;
  format?: "currency" | "percent" | "number" | "compact" | "statusBadge";
}

export interface DenseTableProps<T> {
  data: T[];
  columns: Column<T>[];
  searchPlaceholder?: string;
  searchableKeys?: (keyof T)[];
  emptyMessage?: string;
  className?: string;
}

export function DenseTable<T extends Record<string, any>>({
  data,
  columns,
  searchPlaceholder = "Buscar...",
  searchableKeys,
  emptyMessage = "Nenhum registro encontrado.",
  className,
}: DenseTableProps<T>) {
  const [query, setQuery] = useState("");

  const filteredData = useMemo(() => {
    if (!query.trim()) return data;
    const q = query.toLowerCase();
    return data.filter((row) => {
      const keysToSearch = searchableKeys || (Object.keys(row) as (keyof T)[]);
      return keysToSearch.some((k) => {
        const val = row[k];
        return val !== null && val !== undefined && String(val).toLowerCase().includes(q);
      });
    });
  }, [data, query, searchableKeys]);

  const renderCellValue = (col: Column<T>, row: T) => {
    const raw = col.accessorKey ? row[col.accessorKey] : undefined;
    if (raw === null || raw === undefined) return "-";

    if (col.format === "currency") {
      const num = typeof raw === "number" ? raw : parseFloat(String(raw).replace(",", ".")) || 0;
      return fmtCurrency(num);
    }
    if (col.format === "compact") {
      const num = typeof raw === "number" ? raw : parseFloat(String(raw).replace(",", ".")) || 0;
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
    if (col.format === "statusBadge") {
      const valStr = String(raw);
      const isDanger = valStr === "true" || valStr === "excesso" || valStr === "Acima do Limite";
      const isWarning = valStr === "baixa" || valStr === "Subexecutado";
      return (
        <Badge variant={isDanger ? "danger" : isWarning ? "warning" : "success"}>
          {valStr}
        </Badge>
      );
    }

    return String(raw);
  };

  return (
    <div className={clsx("bg-white border border-borderLine rounded-xl overflow-hidden", className)}>
      {searchableKeys !== undefined && (
        <div className="p-3 border-b border-borderLine bg-gray-50/50 flex items-center gap-2">
          <Search className="w-4 h-4 text-mutedText shrink-0" />
          <input
            type="text"
            value={query}
            onChange={(e) => setQuery(e.target.value)}
            placeholder={searchPlaceholder}
            className="w-full bg-transparent text-xs text-ink focus:outline-none placeholder:text-mutedText"
          />
        </div>
      )}
      <div className="overflow-x-auto">
        <table className="w-full text-xs text-left border-collapse">
          <thead>
            <tr className="border-b border-borderLine bg-gray-100/70 text-subtleText uppercase tracking-wider font-semibold">
              {columns.map((col, idx) => (
                <th
                  key={idx}
                  className={clsx(
                    "px-4 py-2.5",
                    col.align === "right" && "text-right",
                    col.align === "center" && "text-center"
                  )}
                >
                  {col.header}
                </th>
              ))}
            </tr>
          </thead>
          <tbody className="divide-y divide-gray-100">
            {filteredData.length === 0 ? (
              <tr>
                <td colSpan={columns.length} className="px-4 py-6 text-center text-mutedText italic">
                  {emptyMessage}
                </td>
              </tr>
            ) : (
              filteredData.map((row, rIdx) => (
                <tr key={rIdx} className="hover:bg-gray-50/80 transition-colors">
                  {columns.map((col, cIdx) => (
                    <td
                      key={cIdx}
                      className={clsx(
                        "px-4 py-2 text-ink whitespace-nowrap",
                        col.align === "right" && "text-right",
                        col.align === "center" && "text-center",
                        (col.isSerifNumeric || col.format === "currency" || col.format === "compact") &&
                          "font-serif font-semibold"
                      )}
                    >
                      {renderCellValue(col, row)}
                    </td>
                  ))}
                </tr>
              ))
            )}
          </tbody>
        </table>
      </div>
    </div>
  );
}
