import type React from "react";
import { cn } from "../utils/cn";
import { fmtCompact } from "../utils/formatters";

export interface OriginBreakdownItem {
  label: string;
  amountPerReal?: string;
  percentage: number;
  colorClass?: string;
}

export interface HeroFiscalCardProps {
  cityName?: string;
  periodText?: string;
  headline?: React.ReactNode;
  summary?: React.ReactNode;
  totalArrecadado?: string | number;
  previstoTotal?: string | number;
  realizationPercent?: number;
  statusBadgeText?: string;
  originBreakdown?: OriginBreakdownItem[];
  arrecadadoTitle?: string;
  className?: string;
}

export function HeroFiscalCard({
  cityName,
  periodText,
  headline,
  summary,
  totalArrecadado,
  previstoTotal,
  realizationPercent = 0,
  statusBadgeText,
  originBreakdown,
  arrecadadoTitle,
  className,
}: HeroFiscalCardProps) {
  const formattedTotal =
    typeof totalArrecadado === "number"
      ? fmtCompact(totalArrecadado)
      : (totalArrecadado ?? "R$ 0");

  const formattedPrevisto =
    typeof previstoTotal === "number"
      ? fmtCompact(previstoTotal)
      : (previstoTotal ?? "R$ 0");

  const displayHeadline =
    headline ??
    (cityName
      ? `Panorama das contas públicas de ${cityName}`
      : "Panorama das Contas Públicas");

  const displaySummary =
    summary ??
    "Acompanhe em tempo real a arrecadação de receitas, aplicação dos recursos orçamentários, despesas detalhadas e indicadores fiscais do município.";

  return (
    <div
      className={cn(
        "grid grid-cols-1 items-start gap-8 lg:grid-cols-12",
        className,
      )}
    >
      {/* Coluna Esquerda: Narrativa */}
      <div className="space-y-4 lg:col-span-7">
        {periodText && (
          <span className="inline-block font-semibold text-accent text-xs tracking-normal">
            {periodText}
          </span>
        )}

        {displayHeadline && (
          <h1 className="font-bold font-serif text-2xl text-ink leading-tight tracking-tight sm:text-3xl lg:text-[32px]">
            {displayHeadline}
          </h1>
        )}

        {displaySummary && (
          <div className="space-y-3 text-sm text-subtleText leading-relaxed sm:text-base">
            {displaySummary}
          </div>
        )}
      </div>

      {/* Coluna Direita: Card Visual */}
      <div className="rounded-[14px] border border-[#e7e9ee] bg-white p-6 shadow-sm lg:col-span-5">
        <div className="mb-4 flex items-center justify-between gap-2">
          <span className="font-medium text-subtleText text-xs">
            {arrecadadoTitle ||
              `Arrecadado no ano até agora ${cityName ? `· ${cityName}` : ""}`}
          </span>
          {statusBadgeText && (
            <span className="inline-flex shrink-0 items-center rounded-full border border-amber-200/80 bg-amber-50 px-2.5 py-0.5 font-medium text-[11px] text-amber-800">
              {statusBadgeText}
            </span>
          )}
        </div>

        <div className="mb-2 font-bold font-serif text-3xl text-ink tracking-tight sm:text-4xl">
          {formattedTotal}
        </div>

        <div className="mb-4 space-y-1.5">
          <div className="flex items-center justify-between font-medium text-subtleText text-xs">
            <span>
              Previsto:{" "}
              <strong className="text-ink">{formattedPrevisto}</strong>
            </span>
            <span className="font-semibold text-accent">
              {realizationPercent}% executado
            </span>
          </div>

          <div className="h-2.5 w-full overflow-hidden rounded-full bg-[#f4f5f7]">
            <div
              className="h-full rounded-full bg-accent transition-all duration-500 ease-out"
              style={{
                width: `${Math.min(100, Math.max(0, realizationPercent))}%`,
              }}
            />
          </div>
        </div>

        {originBreakdown && originBreakdown.length > 0 && (
          <div className="mt-4 border-[#e7e9ee] border-t pt-4">
            <h4 className="mb-3 font-semibold text-ink text-xs">
              De onde vem cada R$ 1,00
            </h4>
            <div className="space-y-3">
              {originBreakdown.map((item) => {
                const colorClass = item.colorClass || "bg-accent";
                return (
                  <div key={item.label} className="space-y-1 text-xs">
                    <div className="flex items-center justify-between text-subtleText">
                      <span className="font-medium text-ink">{item.label}</span>
                      <span className="font-semibold text-ink">
                        {item.amountPerReal ? `${item.amountPerReal} ` : ""}(
                        {item.percentage}%)
                      </span>
                    </div>
                    <div className="h-2 w-full overflow-hidden rounded-full bg-[#f4f5f7]">
                      <div
                        className={cn(
                          "h-full rounded-full transition-all duration-500",
                          colorClass,
                        )}
                        style={{
                          width: `${Math.min(100, Math.max(0, item.percentage))}%`,
                        }}
                      />
                    </div>
                  </div>
                );
              })}
            </div>
          </div>
        )}
      </div>
    </div>
  );
}
