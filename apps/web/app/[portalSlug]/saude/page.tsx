import { getHistoriaSaude } from "@transparencia/db";
import {
  AlertBox,
  fmtCompact,
  getPartialYearPeriod,
  KPICard,
  KPIGrid,
  SaudeContratacaoSection,
  SaudeEmendasSection,
  SaudeFontesDonut,
  SaudeHeroSection,
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
  const { portalSlug } = await params;
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

  return (
    <div className="space-y-12 pb-12">
      {/* Seção 1: Hero (Novo) */}
      <SaudeHeroSection
        ano={selectedYear}
        isCurrentYear={isCurrentYear}
        partialPeriod={partialPeriod}
        orcamento={saude.orcamento}
        fontesReceita={saude.fontesReceita}
      />

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
          O que entrou no Fundo
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
