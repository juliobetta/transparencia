import { getHistoriaSaude } from "@transparencia/db";
import {
  AlertBox,
  DenseTable,
  fmtCompact,
  fmtPercent,
  getPartialYearPeriod,
  KPICard,
  KPIGrid,
  SaudeFontesDonut,
  SaudeTrendChart,
} from "@transparencia/ui";

export const dynamic = "force-dynamic";

interface SaudePageProps {
  params: Promise<{ portalSlug: string }>;
  searchParams: Promise<{ ano?: string; entidades?: string }>;
}

export default async function SaudePage({
  params,
  searchParams,
}: SaudePageProps) {
  const { portalSlug: _portalSlug } = await params;
  const resolvedSearchParams = await searchParams;

  const currentYear = new Date().getFullYear();
  const selectedYear = resolvedSearchParams.ano
    ? Number(resolvedSearchParams.ano)
    : currentYear;
  const entidadesIds = resolvedSearchParams.entidades
    ? resolvedSearchParams.entidades.split(",").filter(Boolean)
    : undefined;

  const isCurrentYear = selectedYear === currentYear;
  const partialPeriod = getPartialYearPeriod();

  const saude = await getHistoriaSaude(selectedYear, entidadesIds);

  const emendasCols = [
    { header: "Autor da Emenda", accessorKey: "Autor" as const },
    {
      header: "Objeto",
      accessorKey: "Objeto" as const,
      className: "max-w-[200px]",
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
    <div className="space-y-10">
      {/* Header & Subtitle */}
      <div>
        <p className="mb-1 font-semibold text-slate-500 text-xs uppercase tracking-wider">
          TEMAS · EXERCÍCIO {selectedYear}
          {isCurrentYear ? ` (PARCIAL, ${partialPeriod})` : ""}
        </p>
        <h1 className="font-bold font-serif text-3xl text-slate-900">
          Fundo Municipal de Saúde
        </h1>
        <p className="mt-2 text-slate-600 text-sm">
          Acompanha o dinheiro do Fundo Municipal de Saúde do começo ao fim:{" "}
          <strong className="font-bold text-slate-900">o que entrou</strong>, o
          que foi empenhado, como foi contratado e quem recebeu.
        </p>
      </div>

      {/* Top KPI Grid */}
      <KPIGrid columns={4}>
        <KPICard
          title="Dotação Atualizada"
          value={fmtCompact(saude.orcamento.dotacao)}
          subtext="Orçamento aprovado"
        />
        <KPICard
          title="Total Empenhado"
          value={
            <span className="font-bold text-blue-700">
              {fmtCompact(saude.orcamento.empenhado)}
            </span>
          }
        />
        <KPICard
          title="Taxa de Execução"
          value={fmtPercent(saude.orcamento.taxaExecucao * 100)}
        />
        <KPICard
          title="Medicamentos e Insumos"
          value={fmtCompact(saude.farmaceutica.medicamentosInsumos)}
        />
      </KPIGrid>

      {/* Alert Box if Sub-execution */}
      {saude.orcamento.alertaSubExecucao && (
        <AlertBox type="warning" title="Alerta de Subexecução Orçamentária">
          A execução da Saúde está abaixo de 70% da dotação aprovada para o
          exercício.
        </AlertBox>
      )}

      {/* Section 1: O que entrou no Fundo */}
      <section className="space-y-6 border-[#1a1d21] border-t-2 pt-8">
        <h2 className="font-bold font-serif text-2xl text-slate-900">
          O que entrou no Fundo
        </h2>
        <div className="grid grid-cols-3 gap-6">
          <div className="col-span-2">
            <SaudeFontesDonut data={saude.fontesReceita} ano={selectedYear} />
          </div>
          <div className="flex flex-col gap-4">
            <KPICard
              title="Repasses da Prefeitura ao Fundo"
              value={fmtCompact(saude.fontesReceita.repassesPrefeitura)}
            />
            <KPICard
              title="Emendas parlamentares"
              value={fmtCompact(saude.fontesReceita.emendasParlamentares)}
            />
          </div>
        </div>
      </section>

      {/* Section 2: Empenhado ano a ano */}
      <section className="space-y-6 border-[#1a1d21] border-t-2 pt-8">
        <h2 className="font-bold font-serif text-2xl text-slate-900">
          Empenhado ano a ano
        </h2>
        <SaudeTrendChart
          data={saude.executionTrend}
          selectedYear={selectedYear}
        />
      </section>

      {/* Section 3: Insumos e assistência farmacêutica */}
      <section className="space-y-6 border-[#1a1d21] border-t-2 pt-8">
        <h2 className="font-bold font-serif text-2xl text-slate-900">
          Insumos e assistência farmacêutica
        </h2>
        <div className="grid grid-cols-1 gap-4 md:grid-cols-3">
          <KPICard
            title="Medicamentos e insumos"
            value={fmtCompact(saude.farmaceutica.medicamentosInsumos)}
            subtext="Subfunção 10.303"
          />
          <KPICard
            title="Judicialização da saúde"
            value={
              <span className="font-bold text-amber-700">
                {fmtCompact(saude.farmaceutica.judicializacao)}
              </span>
            }
            subtext="sentenças judiciais"
          />
          <KPICard
            title="Concentração (HHI)"
            value={
              <span className="font-bold text-amber-600">
                {saude.farmaceutica.hhi.toLocaleString("pt-BR")}
              </span>
            }
            subtext={saude.farmaceutica.hhiClassificacao}
          />
        </div>
      </section>

      {/* Section 4: Emendas Parlamentares Destinadas à Saúde */}
      <section className="space-y-6 border-[#1a1d21] border-t-2 pt-8">
        <h2 className="font-bold font-serif text-2xl text-slate-900">
          Emendas Parlamentares Destinadas à Saúde
        </h2>
        <DenseTable
          data={saude.emendas}
          columns={emendasCols}
          searchableKeys={["Autor", "Objeto"]}
        />
      </section>
    </div>
  );
}
