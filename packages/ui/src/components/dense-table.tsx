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
    | "date";
  className?: string;
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
        return (
          val !== null &&
          val !== undefined &&
          String(val).toLowerCase().includes(q)
        );
      });
    });
  }, [data, query, searchableKeys]);

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
    if (col.format === "statusBadge") {
      const valStr = String(raw);
      const isDanger =
        valStr === "true" ||
        valStr === "excesso" ||
        valStr === "Acima do Limite";
      const isWarning = valStr === "baixa" || valStr === "Subexecutado";
      return (
        <Badge
          variant={isDanger ? "danger" : isWarning ? "warning" : "success"}
        >
          {valStr}
        </Badge>
      );
    }

    return String(raw);
  };

  return (
    <div
      className={cn(
        "overflow-hidden rounded-xl border border-borderLine bg-white",
        className,
      )}
    >
      {searchableKeys !== undefined && (
        <div className="flex items-center gap-2 border-borderLine border-b bg-gray-50/50 p-3">
          <Search className="h-4 w-4 shrink-0 text-mutedText" />
          <input
            type="text"
            value={query}
            onChange={(e) => setQuery(e.target.value)}
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
            {filteredData.length === 0 ? (
              <tr>
                <td
                  colSpan={columns.length}
                  className="px-4 py-6 text-center text-mutedText italic"
                >
                  {emptyMessage}
                </td>
              </tr>
            ) : (
              filteredData.map((row) => (
                <tr
                  key={`row-${row[columns[0].accessorKey as string]}`}
                  className="transition-colors hover:bg-gray-50/80"
                >
                  {columns.map((col) => (
                    <td
                      key={`cell-${row[columns[0].accessorKey as string]}-${col.accessorKey as string}`}
                      className={cn(
                        col.className ? col.className : "whitespace-nowrap",
                        "px-4 py-2 text-ink",
                        col.align === "right" && "text-right",
                        col.align === "center" && "text-center",
                        (col.isSerifNumeric ||
                          col.format === "currency" ||
                          col.format === "compact") &&
                          "font-semibold font-serif",
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
