import { BookOpen, ShieldCheck } from "lucide-react";

export function CaspInfoCard() {
  return (
    <div className="rounded-xl border border-blue-100 bg-gradient-to-r from-blue-50/70 via-indigo-50/30 to-slate-50 p-6 shadow-sm">
      <div className="flex flex-col gap-4 md:flex-row md:items-center md:justify-between">
        <div className="flex items-center gap-3">
          <div className="flex h-10 w-10 shrink-0 items-center justify-center rounded-lg bg-blue-600 text-white shadow-xs">
            <BookOpen className="h-5 w-5" />
          </div>
          <div>
            <div className="flex items-center gap-2">
              <h3 className="font-bold font-serif text-base text-slate-900">
                Enquadramento contábil (PCASP/MCASP)
              </h3>
            </div>
            <p className="text-slate-600 text-xs">
              Classificação das contribuições segundo a Contabilidade Aplicada
              ao Setor Público (NBC TSP)
            </p>
          </div>
        </div>

        <div className="flex flex-wrap items-center gap-2 text-xs">
          <span className="inline-flex items-center gap-1.5 rounded-md border border-slate-200 bg-white px-2.5 py-1 font-medium text-slate-700">
            <ShieldCheck className="h-3.5 w-3.5 text-blue-600" />
            MCASP / STN
          </span>
          <span className="inline-flex items-center gap-1.5 rounded-md border border-slate-200 bg-white px-2.5 py-1 font-medium text-slate-700">
            PCASP — classe 3 (VPD)
          </span>
        </div>
      </div>

      <div className="mt-5 grid grid-cols-1 gap-4 border-blue-100/80 border-t pt-4 sm:grid-cols-3">
        <div className="space-y-1 text-xs">
          <span className="font-semibold text-blue-900">
            1. Orbrigações Patronais (elem. 13)
          </span>
          <p className="text-slate-600 leading-relaxed">
            Encargo social ordinário pago mensalmente pelos órgãos municipais
            sobre a folha de pagamento dos servidores ativos.
          </p>
        </div>

        <div className="space-y-1 text-xs">
          <span className="font-semibold text-amber-900">
            2. Aporte para déficit atuarial (elem. 97)
          </span>
          <p className="text-slate-600 leading-relaxed">
            Recursos suplementares transferidos para a cobertura do déficit
            atuarial, visando o reequilíbrio financeiro do RPPS.
          </p>
        </div>

        <div className="space-y-1 text-xs">
          <span className="font-semibold text-slate-900">
            3. Amortização da dívida (elem. 71)
          </span>
          <p className="text-slate-600 leading-relaxed">
            Pagamentos referentes a termos de acordo e parcelamentos de débitos
            previdenciários repactuados em exercícios anteriores.
          </p>
        </div>
      </div>
    </div>
  );
}
