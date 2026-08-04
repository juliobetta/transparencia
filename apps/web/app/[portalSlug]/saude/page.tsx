import { AlertBox, fmtCompact, KPICard } from "@transparencia/ui";
import { KPIGrid } from "@/components/kpi-grid";
import { SaudeContratacaoSection } from "@/components/saude-contratacao-section";
import { SaudeEmendasSection } from "@/components/saude-emendas-section";
import { SaudeFontesDonut } from "@/components/saude-fontes-donut";
import { SaudeHeroSection } from "@/components/saude-hero-section";
import { SaudeTrendChart } from "@/components/saude-trend-chart";
import { loadSaudeData } from "./loader";
import { buildSaudeViewModel } from "./view-model";

export const dynamic = "force-dynamic";

interface SaudePageProps {
  params: Promise<{ portalSlug: string }>;
  searchParams: Promise<{ ano?: string; entidades?: string }>;
}

export default async function SaudePage({
  params,
  searchParams,
}: SaudePageProps) {
  const { portalSlug } = await params;
  const resolvedSearchParams = await searchParams;
  const rawData = await loadSaudeData(resolvedSearchParams);
  const viewModel = buildSaudeViewModel(rawData);
  const { selectedYear, isCurrentYear, partialPeriod, saude } = viewModel;

  return (
    <div className="space-y-12 pb-12">
      {/* Seção 1: Hero (Novo) */}
      <div className="space-y-8">
        <SaudeHeroSection
          ano={selectedYear}
          isCurrentYear={isCurrentYear}
          partialPeriod={partialPeriod}
          orcamento={saude.orcamento}
          fontesReceita={saude.fontesReceita}
        />

        {/* Hero KPIs com KPIGrid e KPICard */}
        <KPIGrid columns={4}>
          <KPICard
            title="Dotação Atualizada"
            value={fmtCompact(saude.orcamento.dotacao)}
          />
          <KPICard
            title="Contratos vinculados"
            value={saude.orcamento.contratosVinculadosCount}
          />
          <KPICard
            title="Fornecedores ativos"
            value={saude.orcamento.fornecedoresAtivosCount}
          />
          <KPICard
            title="Medicamentos e Insumos"
            value={fmtCompact(saude.orcamento.medicamentosInsumos)}
          />
        </KPIGrid>
      </div>

      {/* Alerta de Subexecução se aplicável */}
      {saude.orcamento.alertaSubExecucao && (
        <AlertBox type="warning" title="Alerta de Subexecução Orçamentária">
          A execução da Saúde está abaixo de 70% da dotação aprovada para o
          exercício.
        </AlertBox>
      )}

      {/* Seção 2: O que entrou no Fundo (Existente) */}
      <section className="space-y-6 border-[#1a1d21] border-t-2 pt-8">
        <h2 className="font-bold font-serif text-2xl text-slate-900">
          O que entrou
        </h2>
        <div className="grid grid-cols-1 gap-6 md:grid-cols-3">
          <div className="md:col-span-2">
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

      {/* Seção 3: Empenhado no ano (Existente) */}
      <section className="space-y-6 border-[#1a1d21] border-t-2 pt-8">
        <h2 className="font-bold font-serif text-2xl text-slate-900">
          Empenhado no ano
        </h2>
        <SaudeTrendChart
          data={saude.executionTrend}
          selectedYear={selectedYear}
        />
      </section>

      {/* Seção 4: Como o Fundo contrata (Novo) */}
      <SaudeContratacaoSection
        portalSlug={portalSlug}
        orcamento={saude.orcamento}
        licitacoesSaude={saude.licitacoesSaude}
      />

      {/* Seção 5: Insumos e assistência farmacêutica (Existente) */}
      <section className="space-y-6 border-[#1a1d21] border-t-2 pt-8">
        <h2 className="font-bold font-serif text-2xl text-slate-900">
          Insumos e assistência farmacêutica
        </h2>
        <KPIGrid columns={3}>
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
        </KPIGrid>
      </section>

      {/* Seção 6: Emendas parlamentares destinadas à Saúde (Existente, com mais detalhes) */}
      <SaudeEmendasSection
        ano={selectedYear}
        emendasStats={saude.emendasStats}
      />
    </div>
  );
}
