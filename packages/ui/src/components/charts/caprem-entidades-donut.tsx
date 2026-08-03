"use client";

import { Pie, PieChart, ResponsiveContainer, Tooltip } from "recharts";
import { fmtCurrency } from "../../utils/formatters";
import { toTitleCase } from "../../utils/text";

export interface EntityCapremItem {
  entidade: string;
  empenhado: number;
  liquidado: number;
  pago: number;
}

export interface CapremEntidadesDonutProps {
  data: EntityCapremItem[];
  ano: number;
  className?: string;
}

const COLOR_PALETTE = [
  "#1976d2", // Blue - Prefeitura
  "#2e7d32", // Green - Fundo de Saúde
  "#b78103", // Gold/Yellow - Fundo de Assistência Social
  "#6b21a8", // Purple - Câmara
  "#0284c7", // Sky blue
  "#059669", // Emerald
  "#64748b", // Slate
];

export function CapremEntidadesDonut({
  data,
  ano,
  className = "",
}: CapremEntidadesDonutProps) {
  const totalPago = data.reduce((acc, item) => acc + item.pago, 0);

  const pieData = data
    .filter((d) => d.pago > 0)
    .map((item, idx) => ({
      name: item.entidade,
      value: item.pago,
      pct: totalPago > 0 ? (item.pago / totalPago) * 100 : 0,
      color: COLOR_PALETTE[idx % COLOR_PALETTE.length],
      fill: COLOR_PALETTE[idx % COLOR_PALETTE.length],
    }));

  return (
    <div
      className={`rounded-xl border border-slate-200 bg-white p-6 shadow-xs ${className}`}
    >
      <div className="mb-4 flex flex-col gap-1 sm:flex-row sm:items-center sm:justify-between">
        <div>
          <h3 className="font-bold font-serif text-base text-slate-900">
            Repasses por Entidade ao CAPREM
          </h3>
          <p className="font-medium text-slate-500 text-xs">
            Distribuição dos recursos repassados pelos órgãos municipais · {ano}
          </p>
        </div>
        <div className="text-right">
          <span className="block font-medium text-[11px] text-slate-400 uppercase tracking-wider">
            Total Repassado
          </span>
          <span className="font-bold font-serif text-blue-900 text-sm">
            {fmtCurrency(totalPago)}
          </span>
        </div>
      </div>

      <div className="flex flex-col items-center justify-between gap-6 sm:flex-row">
        {/* Donut Chart */}
        <div className="h-[200px] w-full min-w-[200px] sm:w-1/2">
          <ResponsiveContainer width="100%" height="100%">
            <PieChart>
              <Pie
                data={pieData}
                cx="50%"
                cy="50%"
                innerRadius={50}
                outerRadius={78}
                paddingAngle={3}
                dataKey="value"
              />
              <Tooltip
                formatter={(val: unknown, name: unknown) => [
                  `${fmtCurrency(Number(val ?? 0))} (${(
                    (Number(val ?? 0) / (totalPago || 1)) * 100
                  ).toFixed(1)}%)`,
                  String(name ?? "Repasse"),
                ]}
                contentStyle={{
                  backgroundColor: "#ffffff",
                  borderColor: "#e2e8f0",
                  borderRadius: "8px",
                  fontSize: "12px",
                  boxShadow: "0 4px 6px -1px rgb(0 0 0 / 0.1)",
                }}
              />
            </PieChart>
          </ResponsiveContainer>
        </div>

        {/* Legend with R$ Values */}
        <div className="flex w-full flex-col justify-center gap-3 sm:w-1/2">
          {pieData.map((item) => (
            <div key={item.name} className="flex items-center gap-3">
              <span
                className="h-3 w-3 shrink-0 rounded-full"
                style={{ backgroundColor: item.color }}
              />
              <div className="flex flex-1 items-center justify-between text-xs">
                <span
                  className="max-w-[400px] truncate font-medium text-slate-700"
                  title={toTitleCase(item.name)}
                >
                  {toTitleCase(item.name)}
                </span>
                <span className="ml-2 shrink-0 font-bold font-serif text-slate-900">
                  {fmtCurrency(item.value)}
                </span>
              </div>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
}
