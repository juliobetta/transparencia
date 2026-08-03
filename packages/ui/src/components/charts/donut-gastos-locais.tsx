import { fmtCompact } from "../../utils/formatters";

export interface DonutGastosLocaisProps {
  localValor: number;
  externoValor: number;
  pctLocal?: number;
  className?: string;
}

export function DonutGastosLocais({
  localValor,
  externoValor,
  pctLocal,
  className = "",
}: DonutGastosLocaisProps) {
  const total = localValor + externoValor;
  const calculatedPct =
    pctLocal !== undefined
      ? pctLocal > 1
        ? pctLocal
        : pctLocal * 100
      : total > 0
        ? (localValor / total) * 100
        : 0;

  // SVG Donut calculations
  const size = 160;
  const strokeWidth = 32;
  const radius = (size - strokeWidth) / 2;
  const circumference = 2 * Math.PI * radius;

  const localRatio = total > 0 ? localValor / total : 0.5;
  const localDash = localRatio * circumference;

  const pctDisplay = `${Math.round(calculatedPct)}%`;

  return (
    <div
      className={`flex flex-col items-center gap-6 rounded-xl border border-borderLine bg-white p-6 sm:flex-row ${className}`}
    >
      <div className="relative flex shrink-0 items-center justify-center">
        <svg
          role="img"
          aria-label={`Gastos locais: ${pctDisplay}`}
          width={size}
          height={size}
          viewBox={`0 0 ${size} ${size}`}
          className="-rotate-90 transform"
        >
          {/* External companies slice (Terracotta / Reddish) */}
          <circle
            cx={size / 2}
            cy={size / 2}
            r={radius}
            fill="transparent"
            stroke="#A85348"
            strokeWidth={strokeWidth}
            strokeDasharray={`${circumference}`}
            strokeDashoffset={0}
          />
          {/* Local companies slice (Green) */}
          <circle
            cx={size / 2}
            cy={size / 2}
            r={radius}
            fill="transparent"
            stroke="#28753C"
            strokeWidth={strokeWidth}
            strokeDasharray={`${localDash} ${circumference}`}
            strokeDashoffset={0}
          />
        </svg>
        {/* Donut Center Label */}
        <div className="absolute flex flex-col items-center justify-center text-center">
          <span className="font-bold text-2xl text-ink leading-none">
            {pctDisplay}
          </span>
          <span className="mt-0.5 font-medium text-subtleText text-xs">
            local
          </span>
        </div>
      </div>

      {/* Legend */}
      <div className="flex w-full flex-col justify-center space-y-4">
        <div className="flex items-start gap-3">
          <div className="mt-1 h-3 w-3 shrink-0 rounded-sm bg-[#28753C]" />
          <div>
            <div className="font-medium text-subtleText text-xs">
              Empresas locais
            </div>
            <div className="font-bold text-ink text-lg">
              {fmtCompact(localValor)}
            </div>
          </div>
        </div>

        <div className="flex items-start gap-3">
          <div className="mt-1 h-3 w-3 shrink-0 rounded-sm bg-[#A85348]" />
          <div>
            <div className="font-medium text-subtleText text-xs">
              Empresas externas
            </div>
            <div className="font-bold text-ink text-lg">
              {fmtCompact(externoValor)}
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
