import {
  DenseTable,
  fmtCompact,
  KPICard,
  toTitleCase,
} from "@transparencia/ui";
import { FunnelExecucaoHorizontal } from "@/components/funil-execucao-horizontal";
import { GastoPorFuncaoBars } from "@/components/gasto-por-funcao-bars";
import { KPIGrid } from "@/components/kpi-grid";
import { loadOrcamentoData } from "./loader";
import { buildOrcamentoViewModel } from "./view-model";

export const dynamic = "force-dynamic";

interface OrcamentoPageProps {
  params: Promise<{ portalSlug: string }>;
  searchParams: Promise<{ ano?: string; entidades?: string }>;
}

export default async function OrcamentoPage({
  params,
  searchParams,
}: OrcamentoPageProps) {
  const { portalSlug } = await params;
  const resolvedSearchParams = await searchParams;
  const rawData = await loadOrcamentoData(portalSlug, resolvedSearchParams);
  const viewModel = buildOrcamentoViewModel(rawData);

  const {
    selectedYear,
    isCurrentYear,
    partialPeriod,
    items,
    totalDotacao,
    totalEmpenhado,
    totalLiquidado,
    totalPago,
    empPct,
    liqPct,
    pagPct,
    funnelStages,
    funcItems,
    orgaosCols,
  } = viewModel;

  return (
    <div className="space-y-6">
      {/* Eyebrow + Título + Subtítulo */}
      <div>
        <span className="inline-block font-semibold text-accent text-xs uppercase tracking-wider">
          ADMINISTRATIVO · EXERCÍCIO {selectedYear}
          {isCurrentYear ? ` (PARCIAL, ${partialPeriod})` : ""}
        </span>
        <h1 className="font-bold font-serif text-3xl text-slate-900">
          Execução Orçamentária
        </h1>
        <p className="mt-2 text-sm text-subtleText leading-relaxed">
          Cada real passa por quatro estágios legais antes de sair do caixa:{" "}
          <strong className="font-semibold text-ink">reservar</strong>{" "}
          (empenho),{" "}
          <strong className="font-semibold text-ink">
            confirmar a entrega
          </strong>{" "}
          (liquidação) e{" "}
          <strong className="font-semibold text-ink">pagar</strong>. Veja quanto
          do orçamento já avançou em cada etapa.
        </p>
      </div>

      <KPIGrid columns={4}>
        <KPICard
          title="Dotação Atualizada"
          value={fmtCompact(totalDotacao)}
          subtext="100% autorizado"
          accent
        />
        <KPICard
          title="Empenhado"
          value={fmtCompact(totalEmpenhado)}
          subtext={`${empPct.toFixed(0)}% da dotação`}
        />
        <KPICard
          title="Liquidado"
          value={fmtCompact(totalLiquidado)}
          subtext={`${liqPct.toFixed(0)}% da dotação`}
        />
        <KPICard
          title="Pago"
          value={fmtCompact(totalPago)}
          subtext={`${pagPct.toFixed(0)}% da dotação`}
        />
      </KPIGrid>

      {/* Funil da Execução */}
      <FunnelExecucaoHorizontal stages={funnelStages} />

      {/* Para onde vai o gasto, por função */}
      {funcItems.length > 0 && (
        <div className="space-y-4 border-ink border-t-2 pt-6">
          <div className="flex items-baseline justify-between">
            <h2 className="font-bold font-serif text-ink text-xl">
              Para onde vai o gasto, por função
            </h2>
            <span className="font-medium text-subtleText text-xs">
              valor pago por função
            </span>
          </div>

          <GastoPorFuncaoBars items={funcItems} />
        </div>
      )}

      {/* Execução por Órgão */}
      <div className="space-y-4 border-ink border-t-2 pt-6">
        <h2 className="font-bold font-serif text-ink text-xl">
          Execução por Órgão e Unidade Gestora
        </h2>
        <DenseTable
          data={items.map((item) => ({
            ...item,
            descricao: toTitleCase(item.descricao),
          }))}
          columns={orgaosCols}
          searchableKeys={["descricao"]}
        />
      </div>
    </div>
  );
}
