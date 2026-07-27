"use client";

import {
  Bar,
  BarChart,
  Cell,
  LabelList,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from "recharts";

export interface ExecutionTrendSaude {
  ano: number;
  empenhado: number;
}

export interface SaudeTrendChartProps {
  data: ExecutionTrendSaude[];
  selectedYear?: number;
  className?: string;
}

interface CustomBarLabelProps {
  x?: number;
  y?: number;
  width?: number;
  value?: number;
}

const renderCustomBarLabel = (props: CustomBarLabelProps) => {
  const { x, y, width, value } = props;
  if (
    value === undefined ||
    value === null ||
    typeof x !== "number" ||
    typeof y !== "number" ||
    typeof width !== "number"
  ) {
    return null;
  }
  const milhoes = value / 1_000_000;
  const formatted = milhoes.toFixed(1).replace(".", ",");
  return (
    <text
      x={x + width / 2}
      y={y - 8}
      fill="#334155"
      textAnchor="middle"
      fontSize={12}
      fontWeight={600}
    >
      {formatted}
    </text>
  );
};

export function SaudeTrendChart({
  data,
  selectedYear,
  className = "",
}: SaudeTrendChartProps) {
  const maxYear =
    data.length > 0 ? Math.max(...data.map((d) => d.ano)) : undefined;
  const activeYear = selectedYear ?? maxYear;

  return (
    <div
      className={`rounded-xl border border-slate-200 bg-white p-6 shadow-sm ${className}`}
    >
      <div className="mb-6 flex items-center justify-between">
        <div>
          <h3 className="font-bold text-base text-slate-900">
            Evolução Orçamentária
          </h3>
          <p className="font-medium text-slate-500 text-xs">
            Total empenhado na Saúde por ano (R$ milhões)
          </p>
        </div>
      </div>

      <div className="h-[220px] w-full pt-4">
        <ResponsiveContainer width="100%" height="100%">
          <BarChart
            data={data}
            margin={{ top: 25, right: 10, left: 10, bottom: 5 }}
          >
            <XAxis
              dataKey="ano"
              tick={{ fill: "#64748b", fontSize: 12 }}
              axisLine={{ stroke: "#e2e8f0" }}
              tickLine={false}
            />
            <YAxis hide />
            <Tooltip
              formatter={(val: unknown) => [
                new Intl.NumberFormat("pt-BR", {
                  style: "currency",
                  currency: "BRL",
                }).format(Number(val ?? 0)),
                "Empenhado",
              ]}
              contentStyle={{
                backgroundColor: "#ffffff",
                borderColor: "#e2e8f0",
                borderRadius: "8px",
                fontSize: "12px",
                boxShadow: "0 4px 6px -1px rgb(0 0 0 / 0.1)",
              }}
            />
            <Bar dataKey="empenhado" radius={[6, 6, 0, 0]}>
              {data.map((entry) => {
                const isSelected = entry.ano === activeYear;
                return (
                  <Cell
                    key={`bar-${entry.ano}`}
                    fill={isSelected ? "#1565c0" : "#2070b4"}
                    opacity={isSelected ? 1 : 0.75}
                  />
                );
              })}
              <LabelList dataKey="empenhado" content={renderCustomBarLabel} />
            </Bar>
          </BarChart>
        </ResponsiveContainer>
      </div>
    </div>
  );
}
