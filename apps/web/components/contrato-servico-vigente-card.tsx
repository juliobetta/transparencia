"use client";

import type { ContratoServicoVigente } from "@transparencia/db";
import { fmtCurrency, fmtDate, fmtPercent } from "@transparencia/ui";

interface ContratoServicoVigenteCardProps {
  contrato: ContratoServicoVigente;
}

export function ContratoServicoVigenteCard({
  contrato,
}: ContratoServicoVigenteCardProps) {
  const {
    fornecedorNome,
    dataInicio,
    vencimentoAtual,
    valorAditado,
    totalEmpenhado,
    totalLiquidado,
    totalPago,
    saldoPendente,
    percentualPago,
  } = contrato;

  const validEmpenhado = Number.isFinite(totalEmpenhado) ? totalEmpenhado : 0;
  const pctLiquidado =
    validEmpenhado > 0 && Number.isFinite(totalLiquidado)
      ? Math.min(100, Math.max(0, (totalLiquidado / validEmpenhado) * 100))
      : 0;
  const pctPago = Number.isFinite(percentualPago)
    ? Math.min(100, Math.max(0, percentualPago))
    : 0;

  const vigenciaText = (() => {
    if (dataInicio && vencimentoAtual) {
      return `${fmtDate(dataInicio)} – ${fmtDate(vencimentoAtual)}`;
    }
    if (vencimentoAtual) {
      return `Até ${fmtDate(vencimentoAtual)}`;
    }
    if (dataInicio) {
      return `A partir de ${fmtDate(dataInicio)}`;
    }
    return "";
  })();

  return (
    <div className="flex flex-col justify-between rounded-xl border border-borderLine bg-white p-5 shadow-xs transition-shadow hover:shadow-sm">
      <div className="space-y-2.5">
        {/* Header: Nome do Fornecedor + Badge */}
        <div className="flex min-h-[40px] items-start justify-between gap-2">
          <h3
            className="line-clamp-2 font-semibold text-ink text-sm leading-snug"
            title={fornecedorNome}
          >
            {fornecedorNome}
          </h3>
          {valorAditado && valorAditado > 0 ? (
            <span
              className="inline-flex shrink-0 items-center whitespace-nowrap rounded-full bg-amber-50 px-2 py-0.5 font-medium text-[10px] text-amber-800 ring-1 ring-amber-600/20 ring-inset"
              title={`Inclui ${fmtCurrency(valorAditado)} em aditivos de valor`}
            >
              Com aditamento
            </span>
          ) : null}
        </div>

        {/* Vigência */}
        <div className="text-subtleText text-xs">
          <span>Vigência: </span>
          <span className="font-medium text-ink">{vigenciaText}</span>
        </div>
      </div>

      {/* Financial Summary */}
      <div className="mt-4 space-y-2 border-gray-100 border-t pt-3">
        <div className="flex items-baseline justify-between text-xs">
          <span className="font-semibold text-[11px] text-mutedText">
            Empenhado:{" "}
            <span className="font-bold font-serif text-ink">
              {fmtCurrency(totalEmpenhado)}
            </span>
          </span>
          <span className="font-semibold text-[11px] text-subtleText">
            Pago:{" "}
            <span className="font-bold font-serif text-emerald-700">
              {fmtCurrency(totalPago)}
            </span>
          </span>
        </div>

        {/* Progress Bar (Empenhado -> Liquidado -> Pago) */}
        <div className="relative h-2 w-full overflow-hidden rounded-full bg-gray-100">
          <div
            className="absolute top-0 bottom-0 left-0 bg-blue-300 transition-all duration-300"
            style={{ width: `${pctLiquidado}%` }}
          />
          <div
            className="absolute top-0 bottom-0 left-0 bg-emerald-500 transition-all duration-300"
            style={{ width: `${pctPago}%` }}
          />
        </div>

        <div className="flex items-baseline justify-between pt-0.5 text-xs">
          <span className="font-medium text-[11px] text-mutedText">
            {fmtPercent(pctPago)} pago
          </span>
          <span className="text-[11px] text-subtleText">
            Saldo:{" "}
            <span className="font-bold font-serif text-warning">
              {fmtCurrency(saldoPendente)}
            </span>
          </span>
        </div>
      </div>
    </div>
  );
}
