import { cn, KPICard } from "@transparencia/ui";
import type { Metadata } from "next";
import { ContratosServicosVigentesSection } from "@/components/contratos-servicos-vigentes-section";
import { DistribucaoModalidadesChart } from "@/components/distribuicao-modalidades-chart";
import { KPIGrid } from "@/components/kpi-grid";
import { LicitacoesTable } from "@/components/licitacoes-table";
import { createPortalMetadata } from "@/lib/metadata";
import { loadLicitacoesData } from "./loader";
import { buildLicitacoesViewModel } from "./view-model";

export const dynamic = "force-dynamic";

interface LicitacoesPageProps {
  params: Promise<{ portalSlug: string }>;
  searchParams: Promise<{ ano?: string; entidades?: string }>;
}

export async function generateMetadata({
  params,
}: LicitacoesPageProps): Promise<Metadata> {
  const { portalSlug } = await params;
  return createPortalMetadata("Licitações", portalSlug, {
    description:
      "Consulta e transparência dos processos licitatórios, contratos públicos e modalidades de contratação municipal.",
    path: "/licitacoes",
    keywords: [
      "licitações municipais",
      "contratos públicos",
      "pregão eletrônico",
      "concorrência",
      "compras públicas",
    ],
  });
}

export default async function LicitacoesPage({
  params,
  searchParams,
}: LicitacoesPageProps) {
  const { portalSlug } = await params;
  const resolvedSearchParams = await searchParams;
  const rawData = await loadLicitacoesData(portalSlug, resolvedSearchParams);
  const viewModel = buildLicitacoesViewModel(rawData);

  const {
    selectedYear,
    isCurrentYear,
    partialPeriod,
    gaps,
    adesao,
    adesaoExterna,
    modalidades,
    acimaLimiteGaps,
    fracionamentoVendorsMap,
    numCasosFracionamento,
    contratosServicosVigentes,
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
          Licitações e Contratos
        </h1>
        <p className="mt-2 max-w-4xl text-slate-600 text-xs leading-relaxed sm:text-sm">
          Contratos sem licitação são comuns e frequentemente legais — dispensas
          de baixo valor e inexigibilidades são permitidas por lei. O ponto de
          atenção são os contratos{" "}
          <strong className="font-semibold text-slate-900">
            acima de R$ 62.725,59 sem licitação
          </strong>
          , que exigem justificativa formal.
        </p>
      </div>

      <KPIGrid columns={4}>
        <KPICard
          title="Acima do limite s/ licitação"
          value={
            <span
              className={cn(acimaLimiteGaps.length > 0 && "text-amber-600")}
            >
              {acimaLimiteGaps.length}
            </span>
          }
          alert={acimaLimiteGaps.length > 0}
          accent
        />
        <KPICard title="Sem processo licitatório" value={gaps.length} />
        <KPICard title="Adesões de ata (carona)" value={adesao.quantidade} />
        <KPICard
          title="Empenhos via ata externa"
          value={adesaoExterna.quantidade}
        />
      </KPIGrid>

      {/* Warning Alert Banner */}
      {numCasosFracionamento > 0 && (
        <div className="flex items-start gap-3 rounded-xl border-amber-500 border-l-4 bg-[#fffaf0] p-4 text-[#7b341e] text-xs shadow-2xs sm:text-sm">
          <span className="mt-0.5 shrink-0 text-base">⚠️</span>
          <div>
            <span className="font-bold text-[#9c4221]">
              {numCasosFracionamento}{" "}
              {numCasosFracionamento === 1 ? "caso" : "casos"} de possível
              fracionamento.
            </span>{" "}
            Fornecedores com 3+ contratos próximos ao limite de dispensa no
            mesmo órgão, sugerindo divisão artificial de compras para evitar
            licitação.
          </div>
        </div>
      )}

      {/* Section 1: Distribuição por modalidade */}
      <section className="space-y-4">
        <div className="flex items-baseline justify-between border-ink border-t-2 pt-8">
          <h2 className="font-bold font-serif text-slate-900 text-xl">
            Distribuição por modalidade
          </h2>
          <span className="font-medium text-slate-400 text-xs">
            valor contratado · quantidade
          </span>
        </div>

        <div className="rounded-2xl border border-slate-200/80 bg-white p-6 shadow-xs">
          {modalidades.length === 0 ? (
            <div className="py-6 text-center text-slate-400 text-xs italic">
              Nenhuma informação de modalidade disponível para o período.
            </div>
          ) : (
            <DistribucaoModalidadesChart data={modalidades} />
          )}
        </div>
      </section>

      {/* Section: Contratos de Serviços Vigentes */}
      <ContratosServicosVigentesSection contratos={contratosServicosVigentes} />

      {/* Section 2: Contratos acima do limite, sem licitação */}
      <section className="space-y-4">
        <div className="border-ink border-t-2 pt-8">
          <div className="flex flex-col justify-between gap-1 sm:flex-row sm:items-baseline">
            <h2 className="font-bold font-serif text-slate-900 text-xl">
              Contratos acima do limite, sem licitação
            </h2>
            <span className="font-medium text-slate-400 text-xs">
              {acimaLimiteGaps.length} contratos · exige justificativa formal
            </span>
          </div>

          <p className="mb-4 text-slate-600 text-xs leading-relaxed sm:text-sm">
            Cada linha merece análise da justificativa oficial. Quando o mesmo
            fornecedor aparece várias vezes com valores próximos ao teto de R$
            62.725,59, pode indicar{" "}
            <strong className="font-semibold text-slate-900">
              fracionamento
            </strong>
            .
          </p>
        </div>

        <LicitacoesTable
          data={acimaLimiteGaps}
          fracionamentoVendors={fracionamentoVendorsMap}
        />
      </section>
    </div>
  );
}
