import { fmtCompact, fmtCurrency, fmtPercent } from "../utils/formatters";
import { toTitleCase } from "../utils/text";
import { DenseTable } from "./dense-table";
import { KPICard } from "./kpi-card";
import { KPIGrid } from "./kpi-grid";

export interface SaudeEmendaItem {
  id: string;
  Nº: string;
  Objeto: string;
  "Valor Autorizado": number;
  Empenhado: number | null;
  Autor: string;
  "Tipo da Emenda": string;
  "Esfera de Origem": string;
  "Ato Normativo": string;
  Destinação: string;
}

export interface SaudeEmendasStatsProps {
  totalAutorizado: number;
  totalEmpenhado: number;
  taxaEmpenho: number;
  maiorEmenda: number;
  lista: SaudeEmendaItem[];
}

export interface SaudeEmendasSectionProps {
  ano: number;
  emendasStats: SaudeEmendasStatsProps;
}

export function SaudeEmendasSection({
  ano,
  emendasStats,
}: SaudeEmendasSectionProps) {
  const countEmendas = emendasStats.lista.length;
  const isZeroEmpenhado = emendasStats.totalEmpenhado === 0;

  const emendasCols = [
    {
      header: "Autor da Emenda",
      accessorKey: "Autor" as const,
      className: "font-bold",
    },
    {
      header: "Objeto",
      accessorKey: "Objeto" as const,
      className: "max-w-[250px]",
    },
    {
      header: "Valor Autorizado",
      accessorKey: "Valor Autorizado" as const,
      align: "right" as const,
      format: "currency" as const,
    },
    {
      header: "Empenhado",
      accessorKey: "Empenhado" as const,
      align: "right" as const,
      format: "currency" as const,
    },
  ];

  return (
    <section className="space-y-6 border-[#1a1d21] border-t-2 pt-8">
      {/* Header */}
      <div className="flex flex-col gap-1 sm:flex-row sm:items-center sm:justify-between">
        <div>
          <h2 className="font-bold font-serif text-2xl text-slate-900">
            Emendas parlamentares destinadas à Saúde
          </h2>
          <p className="mt-1 max-w-3xl text-slate-600 text-sm leading-relaxed">
            Recursos que deputados e senadores destinaram à saúde do município.
            O que importa não é só quanto foi{" "}
            <strong className="font-bold text-slate-900">autorizado</strong>,
            mas se esse dinheiro foi de fato{" "}
            <strong className="font-bold text-slate-900">empenhado</strong> — o
            passo que transforma a promessa em contrato e serviço.
          </p>
        </div>
        <span className="shrink-0 text-slate-500 text-xs">
          {countEmendas} {countEmendas === 1 ? "emenda" : "emendas"} · exercício{" "}
          {ano}
        </span>
      </div>

      {/* Banner de Alerta Vermelho / Salmão */}
      {emendasStats.totalAutorizado > 0 && (
        <div className="flex items-start gap-3 rounded-xl border-rose-600 border-l-4 bg-[#fff5f5] p-4 text-[#8c1d1d] text-xs shadow-2xs sm:text-sm">
          <div>
            <strong className="font-bold">
              {fmtCompact(emendasStats.totalAutorizado)} foram destinados por
              emendas.
            </strong>{" "}
            {isZeroEmpenhado ? (
              <>
                Até agora, <strong className="font-bold">R$ 0</strong> haviam
                sido empenhados. O recurso está disponível, mas ainda não virou
                contrato — sinal de alerta para acompanhar de perto.
              </>
            ) : (
              <>
                Até agora,{" "}
                <strong className="font-bold">
                  {fmtCompact(emendasStats.totalEmpenhado)}
                </strong>{" "}
                foram empenhados ({fmtPercent(emendasStats.taxaEmpenho * 100)}{" "}
                do total).
              </>
            )}
          </div>
        </div>
      )}

      {/* 4 KPI Cards */}
      <KPIGrid columns={4}>
        <KPICard
          title="Total autorizado"
          value={fmtCompact(emendasStats.totalAutorizado)}
        />
        <KPICard
          title="Total empenhado"
          value={
            <span
              className={
                isZeroEmpenhado
                  ? "font-bold text-rose-600"
                  : "font-bold text-slate-900"
              }
            >
              {fmtCompact(emendasStats.totalEmpenhado)}
            </span>
          }
        />
        <KPICard
          title="Taxa de empenho"
          value={
            <span
              className={
                isZeroEmpenhado
                  ? "font-bold text-rose-600"
                  : "font-bold text-slate-900"
              }
            >
              {fmtPercent(emendasStats.taxaEmpenho * 100)}
            </span>
          }
        />
        <KPICard
          title="Maior emenda"
          value={fmtCompact(emendasStats.maiorEmenda)}
        />
      </KPIGrid>

      {/* Tabela Densa com Linha de Totalizador */}
      <div className="space-y-2">
        <DenseTable
          data={emendasStats.lista.map((item) => ({
            ...item,
            Autor: toTitleCase(item.Autor),
            Objeto: toTitleCase(item.Objeto),
          }))}
          columns={emendasCols}
          searchableKeys={["Autor", "Objeto"]}
          rowKey="id"
        />

        {/* Total Summary Footer Row */}
        <div className="flex items-center justify-between rounded-lg bg-slate-100 px-4 py-3 font-bold text-slate-900 text-sm">
          <span>Total</span>
          <div className="flex items-center gap-8">
            <span>
              {fmtCurrency(emendasStats.totalAutorizado)} (Autorizado)
            </span>
            <span
              className={isZeroEmpenhado ? "text-rose-600" : "text-slate-900"}
            >
              {fmtCurrency(emendasStats.totalEmpenhado)} (Empenhado)
            </span>
          </div>
        </div>
      </div>
    </section>
  );
}
