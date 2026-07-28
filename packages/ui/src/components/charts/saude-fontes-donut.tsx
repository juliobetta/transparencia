"use client";

import { Pie, PieChart, ResponsiveContainer, Tooltip } from "recharts";

export interface FontesReceitaSaude {
  uniaoSusPct: number;
  estadoPct: number;
  propriaPct: number;
  repassesPrefeitura?: number;
  emendasParlamentares?: number;
}

export interface SaudeFontesDonutProps {
  data: FontesReceitaSaude;
  ano: number;
  className?: string;
}

export function SaudeFontesDonut({
  data,
  ano,
  className = "",
}: SaudeFontesDonutProps) {
  const hasData =
    data.uniaoSusPct > 0 || data.estadoPct > 0 || data.propriaPct > 0;

  const pieData = hasData
    ? [
        {
          name: "Transferências União (SUS)",
          pct: data.uniaoSusPct,
          color: "#2e7d32", // Green
          fill: "#2e7d32", // Green
        },
        {
          name: "Transferências Estado",
          pct: data.estadoPct,
          color: "#b78103", // Gold/Yellow
          fill: "#b78103", // Gold/Yellow
        },
        {
          name: "Receita própria / repasse",
          pct: data.propriaPct,
          color: "#1976d2", // Blue
          fill: "#1976d2", // Blue
        },
      ]
    : [
        {
          name: "Sem lançamentos de receita no período",
          pct: 100,
          color: "#cbd5e1", // Slate-300
          fill: "#cbd5e1", // Slate-300
        },
      ];

  return (
    <div
      className={`rounded-xl border border-slate-200 bg-white p-6 shadow-sm ${className}`}
    >
      <div className="mb-4">
        <h3 className="font-bold text-base text-slate-900">
          Origem dos Recursos
        </h3>
        <p className="font-medium text-slate-500 text-xs">
          Fontes de receita do Fundo · {ano}
        </p>
      </div>

      <div className="flex flex-col items-center justify-between gap-4 sm:flex-row">
        {/* Donut Chart */}
        <div className="h-[180px] w-full min-w-[180px] sm:w-1/2">
          <ResponsiveContainer width="100%" height="100%">
            <PieChart>
              <Pie
                data={pieData}
                cx="50%"
                cy="50%"
                innerRadius={48}
                outerRadius={72}
                paddingAngle={3}
                dataKey="pct"
              />
              <Tooltip
                formatter={(val: unknown) => [
                  `${Number(val ?? 0)
                    .toFixed(1)
                    .replace(".", ",")}%`,
                  "Participação",
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

        {/* Legend */}
        <div className="flex w-full flex-col justify-center gap-3 sm:w-1/2">
          {pieData.map((item) => (
            <div key={item.name} className="flex items-center gap-2.5">
              <span
                className="h-3 w-3 shrink-0 rounded-full"
                style={{ backgroundColor: item.color }}
              />
              <div className="flex flex-1 items-center justify-between text-xs">
                <span className="font-medium text-slate-700">{item.name}</span>
                <span className="ml-2 font-bold text-slate-900">
                  {item.pct.toFixed(1).replace(".", ",")}%
                </span>
              </div>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
}
