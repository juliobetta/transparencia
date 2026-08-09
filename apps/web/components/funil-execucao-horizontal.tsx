import { fmtCompact } from "@transparencia/ui";

export interface FunnelStage {
  name: string;
  value: number;
  formattedValue?: string;
  colorClass?: string;
}

export interface FunnelExecucaoHorizontalProps {
  stages: FunnelStage[];
}

export function FunnelExecucaoHorizontal({
  stages,
}: FunnelExecucaoHorizontalProps) {
  const maxVal = Math.max(...stages.map((s) => s.value), 1);

  const defaultColors = [
    "bg-blue-600",
    "bg-blue-500",
    "bg-sky-500",
    "bg-cyan-500",
  ];

  return (
    <div className="space-y-4 rounded-[14px] border border-[#e7e9ee] bg-white p-6 shadow-sm">
      <h3 className="font-bold font-serif text-ink text-lg">
        Funil da execução
      </h3>
      <div className="space-y-3">
        {stages.map((stage, idx) => {
          const pct = Math.min(100, Math.max(0, (stage.value / maxVal) * 100));
          const valText = stage.formattedValue || fmtCompact(stage.value);
          const color =
            stage.colorClass || defaultColors[idx % defaultColors.length];

          const isSmall = pct < 15;

          return (
            <div
              key={stage.name}
              className="flex items-center gap-4 font-medium text-xs"
            >
              <span className="w-24 shrink-0 text-subtleText">
                {stage.name}
              </span>
              <div className="relative flex h-9 flex-1 items-center overflow-hidden rounded-md bg-[#eef0f4]">
                <div
                  className={`h-full ${color} flex items-center rounded-md transition-all duration-500 ${isSmall ? "px-2" : "px-4"}`}
                  style={{ width: `${pct}%` }}
                >
                  {!isSmall && (
                    <span className="whitespace-nowrap font-bold text-white text-xs">
                      {valText}
                    </span>
                  )}
                </div>
                {isSmall && (
                  <span className="whitespace-nowrap pl-3 font-bold text-ink text-xs">
                    {valText}
                  </span>
                )}
              </div>
            </div>
          );
        })}
      </div>
    </div>
  );
}
