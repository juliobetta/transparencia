import {
  getExecucaoDecimoTerceiro,
  getFolhaVsServicos,
  getPortalConfig,
} from "@transparencia/db";
import {
  fmtCompact,
  fmtPercent,
  KPICard,
  KPIGrid,
  SectionHeader,
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
  const portalConfig = await getPortalConfig();

  const currentYear = new Date().getFullYear();
  const selectedYear = resolvedSearchParams.ano
    ? Number(resolvedSearchParams.ano)
    : currentYear;
  const entidadesIds = resolvedSearchParams.entidades
    ? resolvedSearchParams.entidades.split(",").filter(Boolean)
    : undefined;

  const isCurrentYear = selectedYear === currentYear;

  const folhaData = await getFolhaVsServicos([selectedYear], entidadesIds);
  const decimo13 = await getExecucaoDecimoTerceiro(selectedYear, entidadesIds);
  const row = folhaData[0] || {
    totalFolha: 0,
    totalPago: 0,
    rclProxy: 0,
    percentualFolha: 0,
  };

  return (
    <div className="space-y-8">
      <div>
        <h1 className="font-bold font-serif text-3xl text-ink">
          Pessoal & Vencimentos
        </h1>
        <p className="mt-1 text-sm text-subtleText">
          Despesas com folha de pagamento, cargos e limites da Lei de
          Responsabilidade Fiscal ({selectedYear}
          {isCurrentYear ? " · parcial" : ""})
        </p>
      </div>

      <KPIGrid columns={4}>
        <KPICard
          title="Total Folha de Pagamento"
          value={fmtCompact(row.totalFolha)}
          subtext="Proventos brutos"
          accent
        />
        <KPICard
          title="Receita Corrente Líquida"
          value={fmtCompact(row.rclProxy)}
          subtext="Proxy RCL"
        />
        <KPICard
          title="Comprometimento LRF"
          value={fmtPercent(row.percentualFolha)}
          subtext="Limite Máximo LRF: 54.0%"
          alert={row.percentualFolha > 54}
        />
        <KPICard
          title="13º Salário Executado"
          value={decimo13 ? fmtCompact(decimo13.pago) : "N/D"}
          subtext={
            decimo13
              ? `Empenhado: ${fmtCompact(decimo13.empenhado)}`
              : "Sem dados"
          }
        />
      </KPIGrid>

      <div>
        <SectionHeader
          title="Indicadores da Lei de Responsabilidade Fiscal (LRF)"
          description={`Comprometimento dos gastos com pessoal da ${portalConfig?.displayName}`}
        />
        <div className="space-y-4 rounded-xl border border-borderLine bg-white p-6">
          <div className="flex justify-between font-semibold text-ink text-xs">
            <span>
              Comprometimento Atual: {fmtPercent(row.percentualFolha)}
            </span>
            <span>Limite Máximo LRF: 54.00%</span>
          </div>
          <div className="relative h-4 w-full overflow-hidden rounded-md bg-gray-100">
            <div
              className="h-full rounded-md transition-all duration-500"
              style={{
                width: `${Math.min(100, (row.percentualFolha / 54) * 100)}%`,
                backgroundColor:
                  row.percentualFolha > 54
                    ? "oklch(0.55 0.11 25)"
                    : "oklch(0.55 0.11 250)",
              }}
            />
          </div>
          <p className="text-subtleText text-xs">
            A LRF estabelece limite teto de 54% da Receita Corrente Líquida
            (RCL) para o Poder Executivo Municipal.
          </p>
        </div>
      </div>
    </div>
  );
}
