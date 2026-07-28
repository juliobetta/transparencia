import { cn } from "../utils/cn";
import { fmtCompact } from "../utils/formatters";

export interface EmendasCardProps {
  totalEmendas: number;
  pctDoArrecadado: number;
  emendasPix: number;
  emendasIndividuais: number;
  className?: string;
}

export function EmendasCard({
  totalEmendas,
  pctDoArrecadado,
  emendasPix,
  emendasIndividuais,
  className,
}: EmendasCardProps) {
  const pctValue =
    pctDoArrecadado > 1 ? pctDoArrecadado : pctDoArrecadado * 100;
  const formattedPct = `${pctValue.toLocaleString("pt-BR", {
    minimumFractionDigits: 1,
    maximumFractionDigits: 1,
  })}% do arrecadado`;

  const pixPct = totalEmendas > 0 ? (emendasPix / totalEmendas) * 100 : 0;
  const indPct =
    totalEmendas > 0 ? (emendasIndividuais / totalEmendas) * 100 : 0;

  return (
    <div
      className={cn(
        "rounded-2xl border border-purple-200 bg-purple-50/20 p-6 shadow-sm backdrop-blur-xs",
        className,
      )}
    >
      <div className="grid grid-cols-1 items-start gap-6 lg:grid-cols-12">
        {/* Coluna Esquerda: Título, Valor Principal e Nota explicativa */}
        <div className="flex flex-col justify-between space-y-4 lg:col-span-6">
          <div>
            <div className="flex flex-wrap items-center gap-2.5">
              <span className="font-semibold text-purple-900 text-xs uppercase tracking-tight">
                Recebido por emendas parlamentares
              </span>
              <span className="inline-flex items-center rounded-full border border-purple-300/70 bg-purple-100/80 px-2.5 py-0.5 font-semibold text-[11px] text-purple-800 shadow-2xs">
                {formattedPct}
              </span>
            </div>

            <div className="mt-3 font-bold font-serif text-3xl text-purple-950 tracking-tight sm:text-4xl">
              {fmtCompact(totalEmendas)}
            </div>

            <p className="mt-3 text-purple-900/80 text-xs leading-relaxed">
              Recurso extraordinário/político, separado dos repasses
              constitucionais automáticos (FPM, ICMS). Mostra quanto entrou por
              articulação parlamentar.
            </p>
          </div>
        </div>

        {/* Coluna Direita: Linhas de detalhamento */}
        <div className="space-y-3 lg:col-span-6">
          {/* Linha 1: Emendas PIX / Transf. Especiais */}
          <div className="rounded-xl border border-purple-100/90 bg-white/90 p-3.5 shadow-2xs transition-all hover:border-purple-200">
            <div className="mb-1.5 flex items-center justify-between text-xs">
              <span className="font-medium text-slate-700">
                Emendas PIX / Transf. Especiais
              </span>
              <div className="flex items-center gap-2">
                <span className="font-bold text-purple-950">
                  {fmtCompact(emendasPix)}
                </span>
                <span className="font-medium text-[11px] text-purple-700/70">
                  ({pixPct.toFixed(1).replace(".", ",")}% do total)
                </span>
              </div>
            </div>
            <div className="h-2 w-full overflow-hidden rounded-full bg-purple-100/60">
              <div
                className="h-full rounded-full bg-purple-600 transition-all duration-500 ease-out"
                style={{ width: `${Math.min(100, Math.max(0, pixPct))}%` }}
              />
            </div>
          </div>

          {/* Linha 2: Emendas Individuais / de Bancada */}
          <div className="rounded-xl border border-purple-100/90 bg-white/90 p-3.5 shadow-2xs transition-all hover:border-purple-200">
            <div className="mb-1.5 flex items-center justify-between text-xs">
              <span className="font-medium text-slate-700">
                Emendas Individuais / de Bancada
              </span>
              <div className="flex items-center gap-2">
                <span className="font-bold text-purple-950">
                  {fmtCompact(emendasIndividuais)}
                </span>
                <span className="font-medium text-[11px] text-purple-700/70">
                  ({indPct.toFixed(1).replace(".", ",")}% do total)
                </span>
              </div>
            </div>
            <div className="h-2 w-full overflow-hidden rounded-full bg-purple-100/60">
              <div
                className="h-full rounded-full bg-purple-400 transition-all duration-500 ease-out"
                style={{ width: `${Math.min(100, Math.max(0, indPct))}%` }}
              />
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
