import { fmtCompact } from "../utils/formatters";

interface DecimoTerceiroCardProps {
  empenhado: number;
  pago: number;
  pctPago: number;
}

export function DecimoTerceiroCard({
  empenhado,
  pago,
  pctPago,
}: DecimoTerceiroCardProps) {
  const pctInt = Math.min(100, Math.round(pctPago * 100));

  return (
    <div className="rounded-xl border border-slate-200 bg-white p-6 shadow-sm">
      {/* Card Header */}
      <div className="mb-6 flex items-center justify-between">
        <h4 className="font-bold text-lg text-slate-900">13º salário</h4>
      </div>

      {/* Metric Columns */}
      <div className="mb-6 grid grid-cols-1 gap-6 md:grid-cols-3">
        <div>
          <span className="mb-1 block text-slate-500 text-xs">
            Total reservado (ajustado)
          </span>
          <span className="font-bold font-serif text-2xl text-slate-900">
            {fmtCompact(empenhado)}
          </span>
        </div>

        <div>
          <span className="mb-1 block text-slate-500 text-xs">
            Efetivamente pago
          </span>
          <span className="font-bold font-serif text-2xl text-slate-900">
            {fmtCompact(pago)}
          </span>
        </div>

        <div>
          <span className="mb-1 block text-slate-500 text-xs">
            Percentual quitado
          </span>
          <span className="font-bold text-2xl text-emerald-600">{pctInt}%</span>
        </div>
      </div>

      {/* Progress Bar */}
      <div className="h-3 w-full overflow-hidden rounded-full bg-slate-100">
        <div
          className="h-full rounded-full bg-emerald-600 transition-all duration-500"
          style={{ width: `${pctInt}%` }}
        />
      </div>
    </div>
  );
}
