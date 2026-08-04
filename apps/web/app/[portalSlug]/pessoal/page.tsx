import { fmtCompact, fmtPercent, KPICard } from "@transparencia/ui";
import { DecimoTerceiroCard } from "@/components/decimo-terceiro-card";
import { DepartmentalPayrollChart } from "@/components/departmental-payroll-chart";
import { KPIGrid } from "@/components/kpi-grid";
import { ProventosDistributionChart } from "@/components/proventos-distribution-chart";
import { loadPessoalData } from "./loader";
import { buildPessoalViewModel } from "./view-model";

export const dynamic = "force-dynamic";

interface PessoalPageProps {
  params: Promise<{ portalSlug: string }>;
  searchParams: Promise<{ ano?: string; entidades?: string }>;
}

export default async function PessoalPage({
  params,
  searchParams,
}: PessoalPageProps) {
  const { portalSlug } = await params;
  const resolvedSearchParams = await searchParams;
  const rawData = await loadPessoalData(portalSlug, resolvedSearchParams);
  const viewModel = buildPessoalViewModel(rawData);
  const {
    selectedYear,
    isCurrentYear,
    partialPeriod,
    pctChefias,
    decimo13,
    distribuicaoProventos,
    departmentalPayroll,
    currentYearRow,
  } = viewModel;

  return (
    <div className="space-y-8 pb-10">
      {/* Header & Subtitle */}
      <div>
        <span className="inline-block font-semibold text-accent text-xs uppercase tracking-wider">
          ADMINISTRATIVO · EXERCÍCIO {selectedYear}
          {isCurrentYear ? ` (PARCIAL, ${partialPeriod})` : ""}
        </span>
        <h1 className="font-bold font-serif text-3xl text-slate-900">
          Folha de Pagamento
        </h1>
        <p className="mt-2 max-w-4xl text-slate-600 text-xs leading-relaxed sm:text-sm">
          Quanto da receita arrecadada é comprometido com salários e proventos.
          A Lei de Responsabilidade Fiscal limita esse gasto a{" "}
          <strong className="font-semibold text-slate-900">
            54% da receita corrente líquida
          </strong>{" "}
          para o Poder Executivo.
        </p>
      </div>

      {/* 3 Key KPI Cards */}
      <KPIGrid columns={3}>
        <KPICard
          title="Folha / Receita Arrecadada"
          value={fmtPercent(currentYearRow.percentualFolha)}
          subtext={
            currentYearRow.percentualFolha <= 54
              ? "abaixo do teto de 54%"
              : "acima do teto de 54%"
          }
          alert={currentYearRow.percentualFolha > 54}
          accent
        />
        <KPICard
          title="Efetivos no comando das chefias"
          value={pctChefias !== null ? fmtPercent(pctChefias) : "N/D"}
          subtext="cargos de liderança concursados"
        />
        <KPICard
          title="Total pago em folha"
          value={fmtCompact(currentYearRow.totalFolha)}
          subtext={`proventos brutos, ${selectedYear}`}
        />
      </KPIGrid>

      {/* Proventos Distribution Histogram Chart */}
      <ProventosDistributionChart data={distribuicaoProventos} />

      {/* Departmental Payroll (E OUTROS) Chart */}
      <DepartmentalPayrollChart
        data={departmentalPayroll}
        selectedYear={selectedYear}
      />

      {/* 13º Salário Card */}
      {decimo13 ? (
        <DecimoTerceiroCard
          empenhado={decimo13.empenhado}
          pago={decimo13.pago}
          pctPago={decimo13.pctPago}
        />
      ) : (
        <div className="rounded-xl border border-slate-200 bg-white p-6 text-center text-slate-500 text-sm shadow-sm">
          Sem dados de 13º salário para {selectedYear}.
        </div>
      )}
    </div>
  );
}
