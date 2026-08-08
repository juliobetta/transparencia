import { getPartialYearPeriod } from "@transparencia/ui";
import type { loadReceitasData } from "./loader";

type ReceitasRawData = Awaited<ReturnType<typeof loadReceitasData>>;

export function buildReceitasViewModel(raw: ReceitasRawData) {
  const rec = raw.fonte || {
    receitaPropria: 0,
    transferenciasUniao: 0,
    transferenciasEstado: 0,
    total: 0,
    pctPropria: 0,
    pctPropriaPrevisto: 0,
    alertaDependencia: false,
    receitaPropriaPrevisto: 0,
    receitaPropriaArrecadado: 0,
    transferenciasUniaoPrevisto: 0,
    transferenciasUniaoArrecadado: 0,
    transferenciasEstadoPrevisto: 0,
    transferenciasEstadoArrecadado: 0,
    totalPrevisto: 0,
    totalArrecadado: 0,
    pctArrecadado: 0,
    totalPctChange: null,
    emendasTotalArrecadado: 0,
    emendasPixArrecadado: 0,
    emendasIndividuaisArrecadado: 0,
    fpmArrecadado: 0,
    icmsArrecadado: 0,
    issIptuArrecadado: 0,
  };

  const totalArr = rec.totalArrecadado;
  const totalPrev = rec.totalPrevisto;
  const pctArrecadadoAnual = (rec.pctArrecadado || 0) * 100;

  const origensData = [
    {
      fonte: "Transferências da União",
      previsto: rec.transferenciasUniaoPrevisto,
      arrecadado: rec.transferenciasUniaoArrecadado,
      pctRealizado:
        rec.transferenciasUniaoPrevisto > 0
          ? (rec.transferenciasUniaoArrecadado /
              rec.transferenciasUniaoPrevisto) *
            100
          : 0,
    },
    {
      fonte: "Transferências do Estado",
      previsto: rec.transferenciasEstadoPrevisto,
      arrecadado: rec.transferenciasEstadoArrecadado,
      pctRealizado:
        rec.transferenciasEstadoPrevisto > 0
          ? (rec.transferenciasEstadoArrecadado /
              rec.transferenciasEstadoPrevisto) *
            100
          : 0,
    },
    {
      fonte: "Receita própria",
      previsto: rec.receitaPropriaPrevisto,
      arrecadado: rec.receitaPropriaArrecadado,
      pctRealizado:
        rec.receitaPropriaPrevisto > 0
          ? (rec.receitaPropriaArrecadado / rec.receitaPropriaPrevisto) * 100
          : 0,
    },
  ];

  const tableData = [
    {
      fonte: "Receita Própria (Municipal)",
      previsto: rec.receitaPropriaPrevisto,
      arrecadado: rec.receitaPropriaArrecadado,
      pct:
        rec.receitaPropriaPrevisto > 0
          ? (rec.receitaPropriaArrecadado / rec.receitaPropriaPrevisto) * 100
          : 0,
    },
    {
      fonte: "Transferências da União",
      previsto: rec.transferenciasUniaoPrevisto,
      arrecadado: rec.transferenciasUniaoArrecadado,
      pct:
        rec.transferenciasUniaoPrevisto > 0
          ? (rec.transferenciasUniaoArrecadado /
              rec.transferenciasUniaoPrevisto) *
            100
          : 0,
    },
    {
      fonte: "Transferências do Estado",
      previsto: rec.transferenciasEstadoPrevisto,
      arrecadado: rec.transferenciasEstadoArrecadado,
      pct:
        rec.transferenciasEstadoPrevisto > 0
          ? (rec.transferenciasEstadoArrecadado /
              rec.transferenciasEstadoPrevisto) *
            100
          : 0,
    },
    {
      fonte: "Total Orçamentário",
      previsto: rec.totalPrevisto,
      arrecadado: rec.totalArrecadado,
      pct:
        rec.totalPrevisto > 0
          ? (rec.totalArrecadado / rec.totalPrevisto) * 100
          : 0,
      className: "font-semibold bg-gray-200",
    },
  ];

  const variationText = (() => {
    if (rec.totalPctChange === null) {
      return "Orçamento aprovado";
    }

    if (rec.totalPctChange >= 0) {
      return `▲ ${rec.totalPctChange.toFixed(1).replace(".", ",")}% vs. ${raw.context.selectedYear - 1}`;
    }

    if (rec.totalPctChange < 0) {
      return `▼ ${Math.abs(rec.totalPctChange).toFixed(1).replace(".", ",")}% vs. ${raw.context.selectedYear - 1}`;
    }

    return "Orçamento aprovado";
  })();

  return {
    selectedYear: raw.context.selectedYear,
    isCurrentYear: raw.context.isCurrentYear,
    partialPeriod: getPartialYearPeriod(),
    rec,
    totalArr,
    totalPrev,
    pctArrecadadoAnual,
    origensData,
    tableData,
    variationText,
  };
}
