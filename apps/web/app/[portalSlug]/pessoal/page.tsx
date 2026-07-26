import {
  getExecucaoDecimoTerceiro,
  getFolhaVsServicos,
  getPercentualChefiasEfetivas,
} from "@transparencia/db";
import {
  DecimoTerceiroCard,
  FolhaLrfHistoryChart,
  fmtCompact,
  fmtPercent,
  getPartialYearPeriod,
  KPICard,
  KPIGrid,
} from "@transparencia/ui";

export const dynamic = "force-dynamic";

interface PessoalPageProps {
  params: Promise<{ portalSlug: string }>;
  searchParams: Promise<{ ano?: string; entidades?: string }>;
}

export default async function PessoalPage({
  params,
  searchParams,
}: PessoalPageProps) {
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

  // Queries
  const yearsHistory = [
    selectedYear - 4,
    selectedYear - 3,
    selectedYear - 2,
    selectedYear - 1,
    selectedYear,
  ];

  const folhaData = await getFolhaVsServicos(yearsHistory, entidadesIds);
  const pctChefias = await getPercentualChefiasEfetivas(
    selectedYear,
    entidadesIds,
  );
  const decimo13 = await getExecucaoDecimoTerceiro(selectedYear, entidadesIds);

  const currentYearRow = folhaData.find((r) => r.ano === selectedYear) || {
    totalFolha: 0,
    totalPago: 0,
    rclProxy: 0,
    percentualFolha: 0,
  };

  const chartItems = folhaData.map((r) => ({
    ano: r.ano,
    percentualFolha: r.percentualFolha,
    isCurrentYear: r.ano === currentYear,
  }));

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

      {/* Historical LRF Chart */}
      <FolhaLrfHistoryChart data={chartItems} />

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
