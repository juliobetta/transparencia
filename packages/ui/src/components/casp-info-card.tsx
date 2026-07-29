import { FileSpreadsheet, HeartPulse, ShieldCheck } from "lucide-react";
import { fmtCompact } from "../utils/formatters";
import { Badge } from "./badge";

interface CaspInfoCardProps {
  totalCasp?: number;
}

export function CaspInfoCard({ totalCasp = 0 }: CaspInfoCardProps) {
  return (
    <div className="rounded-xl border border-emerald-100 bg-gradient-to-r from-emerald-50/70 via-teal-50/30 to-slate-50 p-6 shadow-sm">
      <div className="flex flex-col gap-4 md:flex-row md:items-center md:justify-between">
        <div className="flex items-center gap-3">
          <div className="flex h-10 w-10 shrink-0 items-center justify-center rounded-lg bg-emerald-600 text-white shadow-xs">
            <HeartPulse className="h-5 w-5" />
          </div>
          <div>
            <div className="flex items-center gap-2">
              <h3 className="font-bold font-serif text-base text-slate-900">
                Caixa de Assistência dos Servidores Públicos (CASP)
              </h3>
              <Badge variant="success">Plano de Saúde</Badge>
            </div>
            <p className="text-slate-600 text-xs">
              Autarquia municipal responsável pela assistência médica e
              hospitalar dos servidores de Porciúncula
            </p>
          </div>
        </div>

        {totalCasp > 0 && (
          <div className="flex flex-col items-start rounded-lg border border-emerald-200 bg-white px-4 py-2 text-right shadow-2xs md:items-end">
            <span className="text-2xs text-slate-500 uppercase tracking-wider">
              Repasse Anual Acumulado
            </span>
            <span className="font-bold font-serif text-emerald-700 text-lg">
              {fmtCompact(totalCasp)}
            </span>
          </div>
        )}
      </div>

      <div className="mt-5 grid grid-cols-1 gap-4 border-emerald-100/80 border-t pt-4 sm:grid-cols-3">
        <div className="space-y-1 text-xs">
          <span className="flex items-center gap-1 font-semibold text-emerald-900">
            <HeartPulse className="h-3.5 w-3.5 text-emerald-600" />
            1. Plano de Saúde & Convênios
          </span>
          <p className="text-slate-600 leading-relaxed">
            Gestão do plano de saúde dos servidores municipais ativos, inativos
            e dependentes cadastrados na CASP.
          </p>
        </div>

        <div className="space-y-1 text-xs">
          <span className="flex items-center gap-1 font-semibold text-blue-900">
            <ShieldCheck className="h-3.5 w-3.5 text-blue-600" />
            2. Diferença para a CAPREM
          </span>
          <p className="text-slate-600 leading-relaxed">
            Enquanto a **CAPREM** gerencia aposentadorias (RPPS), a **CASP**
            cuida exclusivamente da assistência à saúde médica do servidor.
          </p>
        </div>

        <div className="space-y-1 text-xs">
          <span className="flex items-center gap-1 font-semibold text-slate-900">
            <FileSpreadsheet className="h-3.5 w-3.5 text-slate-600" />
            3. Registro Orçamentário (PCASP)
          </span>
          <p className="text-slate-600 leading-relaxed">
            Os recolhimentos ocorrem na folha de pagamento sob a rubrica
            patronal do Elemento 13 e repasses institucionais.
          </p>
        </div>
      </div>
    </div>
  );
}
