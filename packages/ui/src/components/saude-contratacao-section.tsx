import Link from "next/link";
import { fmtCompact, fmtPercent } from "../utils/formatters";
import { KPICard } from "./kpi-card";
import { KPIGrid } from "./kpi-grid";

export interface SaudeContratacaoModalidadeItem {
  nome: string;
  valor: number;
  pct: number;
}

export interface SaudeContratacaoLicitacoesProps {
  adesaoCaronaCount: number;
  adesaoCaronaValor: number;
  empenhosAtaExternaCount: number;
  pagoAtaExternaValor: number;
  modalidades: SaudeContratacaoModalidadeItem[];
}

export interface SaudeContratacaoOrcamentoProps {
  empenhado: number;
  contratosVinculadosCount: number;
  fornecedoresAtivosCount: number;
}

export interface SaudeContratacaoSectionProps {
  portalSlug: string;
  orcamento: SaudeContratacaoOrcamentoProps;
  licitacoesSaude: SaudeContratacaoLicitacoesProps;
}

export function SaudeContratacaoSection({
  portalSlug,
  orcamento,
  licitacoesSaude,
}: SaudeContratacaoSectionProps) {
  const caronaValor = licitacoesSaude.adesaoCaronaValor;
  const caronaPct =
    orcamento.empenhado > 0 ? (caronaValor / orcamento.empenhado) * 100 : 0;

  const barColors: Record<string, string> = {
    "Pregão eletrônico": "bg-accent",
    "Adesão a ata (carona)": "bg-amber-700",
    "Dispensa de licitação": "bg-teal-600",
    Inexigibilidade: "bg-teal-400",
    "Tomada de preços / outros": "bg-teal-300",
  };

  return (
    <section className="space-y-6 border-[#1a1d21] border-t-2 pt-8">
      {/* Header com Link */}
      <div className="flex flex-col gap-2 sm:flex-row sm:items-center sm:justify-between">
        <div>
          <h2 className="font-bold font-serif text-2xl text-slate-900">
            Como o Fundo contrata
          </h2>
          <p className="mt-1 max-w-3xl text-slate-600 text-sm leading-relaxed">
            O que a prefeitura faz com o dinheiro que chega ao Fundo — quantos
            contratos assinou, com quantos fornecedores, e por qual caminho.
            Parte da saúde é comprada{" "}
            <strong className="font-bold text-slate-900">
              na carona de atas de outras prefeituras
            </strong>
            , sem licitação própria do município.
          </p>
        </div>
        <Link
          href={`/${portalSlug}/licitacoes`}
          className="inline-flex shrink-0 items-center font-semibold text-accent text-sm hover:underline"
        >
          Ver todas as licitações &rarr;
        </Link>
      </div>

      {/* Banner de Alerta Âmbar */}
      <div className="flex items-start gap-3 rounded-xl border-amber-600 border-l-4 bg-[#fffaf0] p-4 text-[#7b341e] text-xs shadow-2xs sm:text-sm">
        <div>
          <strong className="font-bold">
            {fmtCompact(caronaValor)} — {fmtPercent(caronaPct)} do empenho do
            Fundo —
          </strong>{" "}
          foram contratados por adesão a atas (carona). Modalidade legal, mas
          que dispensa licitação própria: exige acompanhamento para garantir
          preço e entrega.
        </div>
      </div>

      {/* 4 KPI Cards */}
      <KPIGrid columns={4}>
        <KPICard
          title="Contratos vinculados"
          value={orcamento.contratosVinculadosCount}
          subtext={`com ${orcamento.fornecedoresAtivosCount} fornecedores`}
        />
        <KPICard
          title="Adesões de ata (carona)"
          value={
            <span className="font-bold text-amber-700">
              {licitacoesSaude.adesaoCaronaCount}
            </span>
          }
          subtext={`${fmtCompact(caronaValor)} contratados`}
        />
        <KPICard
          title="Empenhos via ata externa"
          value={licitacoesSaude.empenhosAtaExternaCount}
          subtext="notas de empenho"
        />
        <KPICard
          title="Pago via ata externa"
          value={
            <span className="font-bold text-accent">
              {fmtCompact(licitacoesSaude.pagoAtaExternaValor)}
            </span>
          }
          subtext="já liquidado e pago"
        />
      </KPIGrid>

      {/* Card Visual de Distribuição de Modalidades */}
      <div className="rounded-xl border border-[#e7e9ee] bg-white p-6 shadow-sm">
        <div className="mb-4 flex items-center justify-between">
          <h3 className="font-bold font-serif text-lg text-slate-900">
            Por qual caminho o Fundo contratou
          </h3>
          <span className="text-slate-500 text-xs">
            % do valor empenhado · {fmtCompact(orcamento.empenhado)}
          </span>
        </div>

        <div className="space-y-4">
          {licitacoesSaude.modalidades.map(
            (mod: SaudeContratacaoModalidadeItem) => {
              const colorClass = barColors[mod.nome] || "bg-slate-400";
              return (
                <div key={mod.nome} className="space-y-1">
                  <div className="flex items-center justify-between text-sm">
                    <span className="font-medium text-slate-700">
                      {mod.nome}
                    </span>
                    <span className="font-bold text-slate-900">
                      {fmtCompact(mod.valor)}
                    </span>
                  </div>
                  <div className="h-3 w-full overflow-hidden rounded-md bg-[#f4f5f7]">
                    <div
                      className={`h-full rounded-md transition-all duration-500 ${colorClass}`}
                      style={{
                        width: `${Math.min(100, Math.max(0, mod.pct))}%`,
                      }}
                    />
                  </div>
                </div>
              );
            },
          )}
        </div>
      </div>
    </section>
  );
}
