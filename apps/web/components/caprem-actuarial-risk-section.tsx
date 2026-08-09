"use client";

import { Badge, DenseTable, fmtCurrency, fmtPercent } from "@transparencia/ui";
import { AlertTriangle, CheckCircle2, TrendingUp, Users } from "lucide-react";
import { KPIGrid } from "@/components/kpi-grid";
import { SectionHeader } from "@/components/section-header";

export interface ActuarialRiskSummary {
  totalAporteExigido: number;
  totalAporteQuitado: number;
  romboAporteNaoRepassado: number;
  taxaAdimplenciaAporte: number;
  totalEmpenhadoPatronal?: number;
  totalPagoPatronal?: number;
  romboPatronalNaoRepassado?: number;
  deficitMedioMensal?: number;
  totalAmortizacaoDivida: number;
  variacaoAmortizacaoPct: number;
  servidoresEfetivos: number;
  servidoresTemporariosComissionados: number;
  razaoTemporariosEfetivosPct: number;
}

export interface AnnualActuarialTrend {
  ano: number;
  aporteExigido: number;
  aporteQuitado: number;
  taxaAdimplencia: number;
  amortizacaoDivida: number;
}

export interface CadprevParcelamentoItem {
  numeroCadprev: string;
  descricao: string;
  elemento: string;
  empenhado: number;
  pago: number;
  dataEmpenho?: string;
}

export interface CapremActuarialRiskSectionProps {
  ano: number;
  risk: ActuarialRiskSummary;
  trend: AnnualActuarialTrend[];
  cadprev?: CadprevParcelamentoItem[];
  className?: string;
}

export function CapremActuarialRiskSection({
  ano,
  risk,
  trend,
  cadprev = [],
  className,
}: CapremActuarialRiskSectionProps) {
  const hasDeficitPatronal = (risk.romboPatronalNaoRepassado ?? 0) > 0;

  const trendCols = [
    { header: "Exercício / Ano", accessorKey: "ano" as const },
    {
      header: "Aporte Atuarial Exigido",
      accessorKey: "aporteExigido" as const,
      align: "right" as const,
      format: "currency" as const,
    },
    {
      header: "Aporte Efetuado / Quitado",
      accessorKey: "aporteQuitado" as const,
      align: "right" as const,
      format: "currency" as const,
    },
    {
      header: "Índice de Adimplência",
      accessorKey: "taxaAdimplencia" as const,
      align: "right" as const,
      format: "percent" as const,
    },
    {
      header: "Amortização de Dívida / Parcelamento",
      accessorKey: "amortizacaoDivida" as const,
      align: "right" as const,
      format: "currency" as const,
    },
  ];

  const cadprevCols = [
    {
      header: "Registro CADPREV / Ministério da Previdência",
      accessorKey: "numeroCadprev" as const,
      className: "max-w-[200px]",
    },
    {
      header: "Objeto do Termo de Parcelamento",
      accessorKey: "descricao" as const,
      className: "max-w-sm",
    },
    {
      header: "Empenhado",
      accessorKey: "empenhado" as const,
      align: "right" as const,
      format: "currency" as const,
    },
    {
      header: "Pago / Quitado",
      accessorKey: "pago" as const,
      align: "right" as const,
      format: "currency" as const,
    },
  ];

  return (
    <section className={`space-y-6 ${className || ""}`}>
      <SectionHeader
        title="Sustentabilidade Atuarial e Diagnóstico Previdenciário"
        description="Monitoramento do equilíbrio de longo prazo, cobertura do déficit atuarial (Elemento 97), parcelamentos formalizados no CADPREV (Elemento 71) e retenção de repasses patronais."
      />

      {/* Grid de KPIs de Risco Atuarial */}
      <KPIGrid columns={3}>
        <div className="relative overflow-hidden rounded-xl border border-borderLine bg-white p-5 shadow-xs transition-shadow hover:shadow-md">
          <div className="flex items-center justify-between pb-2">
            <span className="font-semibold text-subtleText text-xs uppercase tracking-wider">
              Déficit de Repasse Mensal ({ano})
            </span>
            {hasDeficitPatronal ? (
              <AlertTriangle className="h-5 w-5 shrink-0 text-rose-500" />
            ) : (
              <CheckCircle2 className="h-5 w-5 shrink-0 text-emerald-500" />
            )}
          </div>
          <div className="font-bold font-serif text-2xl text-ink">
            {fmtCurrency(risk.deficitMedioMensal ?? 0)}{" "}
            <span className="font-normal font-sans text-mutedText text-xs">
              /mês retidos
            </span>
          </div>
          <div className="mt-2 flex flex-wrap items-center gap-2 text-xs">
            {hasDeficitPatronal ? (
              <Badge variant="danger">
                Retenção Patronal:{" "}
                {fmtCurrency(risk.romboPatronalNaoRepassado ?? 0)}
              </Badge>
            ) : (
              <Badge variant="success">Repasses Patronais em Dia</Badge>
            )}
          </div>
        </div>

        <div className="relative overflow-hidden rounded-xl border border-borderLine bg-white p-5 shadow-xs transition-shadow hover:shadow-md">
          <div className="flex items-center justify-between pb-2">
            <span className="font-semibold text-subtleText text-xs uppercase tracking-wider">
              Amortização de Dívidas ({ano})
            </span>
            <TrendingUp className="h-5 w-5 shrink-0 text-blue-500" />
          </div>
          <div className="font-bold font-serif text-2xl text-ink">
            {fmtCurrency(risk.totalAmortizacaoDivida)}
          </div>
          <div className="mt-2 text-mutedText text-xs">
            {risk.variacaoAmortizacaoPct > 0 ? (
              <span className="font-semibold text-amber-700">
                +{risk.variacaoAmortizacaoPct.toFixed(1)}% vs exercício anterior
              </span>
            ) : (
              <span>Resgate de dívidas de parcelamentos repactuados</span>
            )}
          </div>
        </div>

        <div className="relative overflow-hidden rounded-xl border border-borderLine bg-white p-5 shadow-xs transition-shadow hover:shadow-md">
          <div className="flex items-center justify-between pb-2">
            <span className="font-semibold text-subtleText text-xs uppercase tracking-wider">
              Base de Contribuintes ({ano})
            </span>
            <Users className="h-5 w-5 shrink-0 text-indigo-500" />
          </div>
          <div className="font-bold font-serif text-2xl text-ink">
            {risk.servidoresEfetivos}{" "}
            <span className="font-normal font-sans text-mutedText text-sm">
              Servidores Efetivos (RPPS)
            </span>
          </div>
          <div className="mt-2 text-mutedText text-xs">
            <span className="font-medium text-slate-700">
              {risk.servidoresTemporariosComissionados}{" "}
              temporários/comissionados
            </span>
            <div className="text-xs">
              ({fmtPercent(risk.razaoTemporariosEfetivosPct)} recolhem ao
              INSS/RGPS)
            </div>
          </div>
        </div>
      </KPIGrid>

      {/* Tabela de Acordos de Confissão e Parcelamento no CADPREV */}
      {cadprev.length > 0 && (
        <div className="space-y-3">
          <div className="flex items-center gap-2">
            <h4 className="font-semibold font-serif text-slate-800 text-sm">
              Acordos Oficiais de Confissão e Parcelamento de Dívidas (CADPREV /
              Ministério da Previdência)
            </h4>
          </div>
          <DenseTable
            data={cadprev}
            columns={cadprevCols}
            searchableKeys={["numeroCadprev", "descricao"]}
          />
          <p className="text-mutedText text-xs">
            Não inclui multas ou penalidades tributárias pagas a outros credores
            (ex: Receita Federal), mesmo quando relacionadas à contribuição
            previdenciária — apenas acordos formais junto ao CAPREM.
          </p>
        </div>
      )}

      {/* Tabela Histórica da Adimplência do Aporte Atuarial */}
      {trend.length > 0 && (
        <div className="space-y-3">
          <h4 className="font-semibold font-serif text-slate-800 text-sm">
            Evolução Histórica da Cobertura Atuarial e Resgate de Dívidas
            (2021-2026)
          </h4>
          <DenseTable
            data={trend}
            columns={trendCols}
            searchableKeys={["ano"]}
          />
        </div>
      )}
    </section>
  );
}
