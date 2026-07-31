"use client";

import ReactECharts from "echarts-for-react";
import { fmtCurrency } from "../../utils/formatters";

export interface FunnelItem {
  name: string;
  value: number;
}

export interface FunnelWaterfallProps {
  data: FunnelItem[];
  title?: string;
  height?: number;
}

export function FunnelWaterfall({
  data,
  title,
  height = 300,
}: FunnelWaterfallProps) {
  const option = {
    title: title
      ? {
          text: title,
          textStyle: {
            fontFamily: "Source Serif 4, Georgia, serif",
            fontSize: 14,
            fontWeight: "bold",
            color: "#1a1d21",
          },
        }
      : undefined,
    tooltip: {
      trigger: "item",
      formatter: (params: any) => {
        return `${params.name}: <b>${fmtCurrency(params.value)}</b>`;
      },
    },
    series: [
      {
        name: "Execução Orçamentária",
        type: "funnel",
        left: "10%",
        top: 40,
        bottom: 20,
        width: "80%",
        min: 0,
        maxSize: "100%",
        sort: "descending",
        gap: 4,
        label: {
          show: true,
          position: "inside",
          formatter: "{b}: {c}",
          fontFamily: "IBM Plex Sans, sans-serif",
          fontSize: 12,
        },
        itemStyle: {
          borderColor: "#fff",
          borderWidth: 1,
        },
        data: data.map((d, i) => ({
          name: d.name,
          value: d.value,
          itemStyle: {
            color:
              i === 0
                ? "oklch(0.55 0.11 250)"
                : i === 1
                  ? "oklch(0.60 0.11 240)"
                  : i === 2
                    ? "oklch(0.65 0.11 230)"
                    : "oklch(0.50 0.13 145)",
          },
        })),
      },
    ],
  };

  return <ReactECharts option={option} style={{ height }} />;
}
