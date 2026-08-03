import { cn } from "../utils/cn";
import { fmtCompact } from "../utils/formatters";

export interface CarrosChefeArrecadacaoProps {
  fpm: number;
  icms: number;
  issIptu: number;
  totalArrecadado: number;
  className?: string;
}

export function CarrosChefeArrecadacao({
  fpm,
  icms,
  issIptu,
  totalArrecadado,
  className,
}: CarrosChefeArrecadacaoProps) {
  const items = [
    {
      label: "FPM · Fundo de Participação dos Municípios",
      shortLabel: "FPM",
      value: fpm,
      color: "bg-emerald-600",
      badgeColor: "bg-emerald-100 text-emerald-800 border-emerald-200",
    },
    {
      label: "ICMS · cota-parte estadual",
      shortLabel: "ICMS",
      value: icms,
      color: "bg-sky-600",
      badgeColor: "bg-sky-100 text-sky-800 border-sky-200",
    },
    {
      label: "ISS + IPTU · tributos municipais",
      shortLabel: "ISS + IPTU",
      value: issIptu,
      color: "bg-indigo-600",
      badgeColor: "bg-indigo-100 text-indigo-800 border-indigo-200",
    },
  ];

  const maxVal = Math.max(...items.map((i) => i.value), 1);

  return (
    <div
      className={cn(
        "rounded-[14px] border border-[#e7e9ee] bg-white p-6 shadow-sm",
        className,
      )}
    >
      <div className="mb-6">
        <h3 className="font-bold font-serif text-ink text-xl tracking-tight sm:text-2xl">
          Os 3 carros-chefe da arrecadação
        </h3>
        <p className="mt-1 text-sm text-subtleText leading-relaxed">
          De onde vem, de verdade, a maior parte do dinheiro — sem as rubricas
          contábeis.
        </p>
      </div>

      <div className="space-y-5">
        {items.map((item) => {
          const pctOfTotal =
            totalArrecadado > 0 ? (item.value / totalArrecadado) * 100 : 0;
          const barWidth = (item.value / maxVal) * 100;

          return (
            <div key={item.label} className="space-y-2">
              <div className="flex flex-wrap items-center justify-between gap-2 text-xs sm:text-sm">
                <div className="flex items-center gap-2.5">
                  <span className="font-semibold text-slate-800">
                    {item.label}
                  </span>
                </div>

                <div className="flex items-center gap-2">
                  <span className="font-bold font-serif text-base text-ink">
                    {fmtCompact(item.value)}
                  </span>
                  <span className="font-medium text-subtleText text-xs">
                    ({pctOfTotal.toFixed(1).replace(".", ",")}% do total)
                  </span>
                </div>
              </div>

              <div className="h-3 w-full overflow-hidden rounded-full bg-[#f4f5f7]">
                <div
                  className={cn(
                    "h-full rounded-full transition-all duration-500 ease-out",
                    item.color,
                  )}
                  style={{
                    width: `${Math.min(100, Math.max(0, barWidth))}%`,
                  }}
                />
              </div>
            </div>
          );
        })}
      </div>
    </div>
  );
}
