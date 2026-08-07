import { DenseTable } from "@transparencia/ui";
import type { Metadata } from "next";
import { CardsSecundariosVisaoGeral } from "@/components/cards-secundarios-visao-geral";
import { HeroFiscalCard } from "@/components/hero-fiscal-card";
import { PipelineExecucao } from "@/components/pipeline-execucao";
import { createPortalMetadata } from "@/lib/metadata";
import { loadVisaoGeralData } from "./loader";
import { buildVisaoGeralViewModel } from "./view-model";

export const dynamic = "force-dynamic";

interface VisaoGeralPageProps {
  params: Promise<{ portalSlug: string }>;
  searchParams: Promise<{ ano?: string; entidades?: string }>;
}

export async function generateMetadata({
  params,
}: VisaoGeralPageProps): Promise<Metadata> {
  const { portalSlug } = await params;
  return createPortalMetadata("Visão Geral", portalSlug);
}

export default async function VisaoGeralPage({
  params,
  searchParams,
}: VisaoGeralPageProps) {
  const { portalSlug } = await params;
  const resolvedSearchParams = await searchParams;

  const rawData = await loadVisaoGeralData(portalSlug, resolvedSearchParams);
  const viewModel = buildVisaoGeralViewModel(rawData);

  return (
    <div className="space-y-9">
      <HeroFiscalCard
        portalName={viewModel.portalName}
        periodText={viewModel.periodText}
        headline={viewModel.heroHeadline}
        summary={viewModel.heroSummary}
        arrecadadoTitle={viewModel.arrecadadoTitle}
        totalArrecadado={viewModel.totalArrecadado}
        previstoTotal={viewModel.previstoTotal}
        realizationPercent={viewModel.realizationPercent}
        originBreakdown={viewModel.originBreakdown}
      />

      <PipelineExecucao
        stages={viewModel.pipelineStages}
        detailUrl={viewModel.orcamentoDetailUrl}
      />

      <CardsSecundariosVisaoGeral
        despesas={viewModel.despesasCardData}
        licitacoes={viewModel.licitacoesCardData}
        pessoal={viewModel.pessoalCardData}
      />

      {viewModel.sanitizedCredores.length > 0 && (
        <div className="space-y-3">
          <div className="flex items-baseline justify-between border-[#1a1d21] border-t-2 pt-3">
            <h3 className="font-bold font-serif text-ink text-xl">
              Maiores Credores da Gestão Atual
            </h3>
            <span className="font-medium text-subtleText text-xs">
              Restos a pagar acumulados até {viewModel.selectedYear}
            </span>
          </div>
          <DenseTable
            data={viewModel.sanitizedCredores}
            columns={viewModel.credoresCols}
          />
        </div>
      )}
    </div>
  );
}
