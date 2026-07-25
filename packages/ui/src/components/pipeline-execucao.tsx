import Link from "next/link";
import React from "react";
import { cn } from "../utils/cn";

export interface ExecutionStage {
  name: string;
  value?: number | string;
  formattedValue: string;
  percentage: number;
  label: string;
  color?: string;
}

export interface PipelineExecucaoProps {
  title?: string;
  detailUrl?: string;
  stages?: ExecutionStage[];
  className?: string;
}

export function PipelineExecucao({
  title = "Do orçamento autorizado ao pagamento",
  detailUrl = "/orcamento",
  stages = [],
  className,
}: PipelineExecucaoProps) {
  const hasStages = stages.length > 0;

  return (
    <div className={cn("w-full", className)}>
      {/* Cabeçalho de Seção */}
      <div className="mb-3.5 flex items-baseline justify-between border-[#1a1d21] border-t-2 pt-3">
        <h3 className="font-bold font-serif text-ink text-xl">{title}</h3>
        {detailUrl && (
          <Link
            href={detailUrl}
            className="inline-flex shrink-0 items-center gap-1 font-semibold text-accent text-xs hover:underline"
          >
            Ver detalhes →
          </Link>
        )}
      </div>

      {/* Container Principal */}
      <div className="rounded-[14px] border border-[#e7e9ee] bg-white p-6 shadow-sm">
        {hasStages ? (
          <div className="flex flex-col items-stretch justify-between gap-4 md:flex-row md:gap-2">
            {stages.map((stage, idx) => (
              <React.Fragment key={stage.name}>
                <div className="flex min-w-0 flex-1 flex-col justify-between">
                  <div>
                    <div className="mb-2 font-semibold text-ink text-xs">
                      {stage.name}
                    </div>
                    <div className="mb-3 h-2.5 w-full overflow-hidden rounded-full bg-[#f4f5f7]">
                      <div
                        className={cn(
                          "h-full rounded-full transition-all duration-500",
                          stage.color || "bg-accent",
                        )}
                        style={{
                          width: `${Math.min(100, Math.max(0, stage.percentage))}%`,
                        }}
                      />
                    </div>
                  </div>
                  <div>
                    <div className="font-bold font-serif text-ink text-lg tracking-tight">
                      {stage.formattedValue}
                    </div>
                    <div className="mt-0.5 font-medium text-subtleText text-xs">
                      {stage.label}
                    </div>
                  </div>
                </div>

                {idx < stages.length - 1 && (
                  <div className="hidden select-none items-center justify-center px-2 text-[#c7ccd4] text-lg md:flex">
                    ›
                  </div>
                )}
              </React.Fragment>
            ))}
          </div>
        ) : (
          <div className="py-6 text-center text-subtleText text-xs">
            Nenhuma etapa de execução orçamentária disponível.
          </div>
        )}
      </div>
    </div>
  );
}
