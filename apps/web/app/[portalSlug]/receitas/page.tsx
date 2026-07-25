import { getFontesReceita, getPortalConfig } from "@transparencia/db";
import {
  AlertBox,
  DenseTable,
  fmtCompact,
  fmtPercent,
  getPartialYearPeriod,
  PrevistoVsArrecadadoOrigem,
} from "@transparencia/ui";

export const dynamic = "force-dynamic";

interface ReceitasPageProps {
  params: Promise<{ portalSlug: string }>;
  searchParams: Promise<{ ano?: string; entidades?: string }>;
}

export default async function ReceitasPage({
  params,
  searchParams,
}: ReceitasPageProps) {
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

  const _portalConfig = await getPortalConfig();

  const fontes = await getFontesReceita([selectedYear], entidadesIds);
  const rec = fontes[0] || {
    receita_propria: 0,
    transferencias_uniao: 0,
    transferencias_estado: 0,
    total: 0,
    pct_propria: 0,
    alerta_dependencia: false,
    receita_propria_previsto: 0,
    receita_propria_arrecadado: 0,
    transferencias_uniao_previsto: 0,
    transferencias_uniao_arrecadado: 0,
    transferencias_estado_previsto: 0,
    transferencias_estado_arrecadado: 0,
    total_previsto: 0,
    total_arrecadado: 0,
    pct_arrecadado: 0,
    total_pct_change: null,
  };

  const totalArr = rec.total_arrecadado;
  const totalPrev = rec.total_previsto;
  const pctArrecadadoAnual = (rec.pct_arrecadado || 0) * 100;

  const partialPeriod = getPartialYearPeriod();

  const origensData = [
    {
      fonte: "Transferências da União",
      previsto: rec.transferencias_uniao_previsto,
      arrecadado: rec.transferencias_uniao_arrecadado,
      pctRealizado:
        rec.transferencias_uniao_previsto > 0
          ? (rec.transferencias_uniao_arrecadado /
              rec.transferencias_uniao_previsto) *
            100
          : 0,
    },
    {
      fonte: "Transferências do Estado",
      previsto: rec.transferencias_estado_previsto,
      arrecadado: rec.transferencias_estado_arrecadado,
      pctRealizado:
        rec.transferencias_estado_previsto > 0
          ? (rec.transferencias_estado_arrecadado /
              rec.transferencias_estado_previsto) *
            100
          : 0,
    },
    {
      fonte: "Receita própria",
      previsto: rec.receita_propria_previsto,
      arrecadado: rec.receita_propria_arrecadado,
      pctRealizado:
        rec.receita_propria_previsto > 0
          ? (rec.receita_propria_arrecadado / rec.receita_propria_previsto) *
            100
          : 0,
    },
  ];

  const tableData = [
    {
      fonte: "Receita Própria (Municipal)",
      previsto: rec.receita_propria_previsto,
      arrecadado: rec.receita_propria_arrecadado,
      pct:
        rec.receita_propria_previsto > 0
          ? (rec.receita_propria_arrecadado / rec.receita_propria_previsto) *
            100
          : 0,
    },
    {
      fonte: "Transferências da União",
      previsto: rec.transferencias_uniao_previsto,
      arrecadado: rec.transferencias_uniao_arrecadado,
      pct:
        rec.transferencias_uniao_previsto > 0
          ? (rec.transferencias_uniao_arrecadado /
              rec.transferencias_uniao_previsto) *
            100
          : 0,
    },
    {
      fonte: "Transferências do Estado",
      previsto: rec.transferencias_estado_previsto,
      arrecadado: rec.transferencias_estado_arrecadado,
      pct:
        rec.transferencias_estado_previsto > 0
          ? (rec.transferencias_estado_arrecadado /
              rec.transferencias_estado_previsto) *
            100
          : 0,
    },
  ];

  const tableCols = [
    { header: "Origem da Receita", accessorKey: "fonte" as const },
    {
      header: "Previsto (R$)",
      accessorKey: "previsto" as const,
      align: "right" as const,
      format: "currency" as const,
    },
    {
      header: "Arrecadado (R$)",
      accessorKey: "arrecadado" as const,
      align: "right" as const,
      format: "currency" as const,
    },
    {
      header: "Execução (%)",
      accessorKey: "pct" as const,
      align: "right" as const,
      format: "percent" as const,
    },
  ];

  const variationText =
    rec.total_pct_change != null
      ? rec.total_pct_change >= 0
        ? `▲ ${rec.total_pct_change.toFixed(1).replace(".", ",")}% vs. ${selectedYear - 1}`
        : `▼ ${Math.abs(rec.total_pct_change).toFixed(1).replace(".", ",")}% vs. ${selectedYear - 1}`
      : "Orçamento aprovado";

  return (
    <div className="space-y-6">
      {/* Eyebrow + Título + Subtítulo */}
      <div>
        <span className="inline-block font-semibold text-accent text-xs uppercase tracking-wider">
          ADMINISTRATIVO · EXERCÍCIO {selectedYear}
          {isCurrentYear ? ` (PARCIAL, ${partialPeriod})` : ""}
        </span>
        <h1 className="mt-1 font-bold font-serif text-3xl text-ink lg:text-4xl">
          Fontes de Receita
        </h1>
        <p className="mt-2 text-sm text-subtleText">
          Compara o que a prefeitura{" "}
          <strong className="font-semibold text-ink">planejou arrecadar</strong>{" "}
          (previsão da LOA) com o que{" "}
          <strong className="font-semibold text-ink">
            efetivamente entrou
          </strong>{" "}
          no caixa, por origem do recurso.
        </p>
      </div>

      {/* Banner Informativo para Ano Parcial */}
      {isCurrentYear && (
        <div className="rounded-xl border border-[#dfe9f8] bg-[#eef4fd] p-4 text-[#3a5a86] text-xs">
          <strong>
            {selectedYear} exibe arrecadação real parcial ({partialPeriod}).
          </strong>{" "}
          Não é diretamente comparável aos anos anteriores, que mostram previsão
          orçamentária anual.
        </div>
      )}

      {/* Grid de 2 Cards Principais (Previsão LOA vs Total Arrecadado) */}
      <div className="grid grid-cols-1 gap-4 md:grid-cols-2">
        {/* Card 1: Previsão Orçamentária (LOA) */}
        <div className="rounded-[14px] border border-[#e7e9ee] bg-white p-5 shadow-sm">
          <div className="text-subtleText text-xs">
            Previsão Orçamentária (LOA)
          </div>
          <div className="mt-2 font-bold font-serif text-3xl text-ink tracking-tight lg:text-4xl">
            {fmtCompact(totalPrev)}
          </div>
          <div className="mt-2 font-medium text-subtleText text-xs">
            {variationText}
          </div>
        </div>

        {/* Card 2: Total Arrecadado Real */}
        <div className="rounded-[14px] border border-[#e7e9ee] bg-white p-5 shadow-sm">
          <div className="text-subtleText text-xs">Total Arrecadado Real</div>
          <div className="mt-2 font-bold font-serif text-3xl text-emerald-700 tracking-tight lg:text-4xl">
            {fmtCompact(totalArr)}
          </div>
          <div className="mt-2 font-medium text-subtleText text-xs">
            {isCurrentYear
              ? "arrecadado acumulado até a data"
              : `exercício ${selectedYear}`}
          </div>
        </div>
      </div>

      {/* Card de Progresso de Arrecadação Anual */}
      <div className="space-y-2 rounded-[14px] border border-[#e7e9ee] bg-white p-5 shadow-sm">
        <div className="flex items-center justify-between font-semibold text-ink text-sm">
          <span>Progresso de arrecadação anual</span>
          <span className="font-bold">{fmtPercent(pctArrecadadoAnual)}</span>
        </div>
        <div className="h-3.5 w-full overflow-hidden rounded-full bg-[#eef0f4]">
          <div
            className="h-full rounded-full bg-accent transition-all duration-500"
            style={{
              width: `${Math.min(100, Math.max(0, pctArrecadadoAnual))}%`,
            }}
          />
        </div>
      </div>

      {/* Previsto vs. Arrecadado por Origem */}
      <div className="space-y-4 border-ink border-t-2 pt-6">
        <div className="flex items-baseline justify-between">
          <h2 className="font-bold font-serif text-ink text-xl">
            Previsto vs. arrecadado por origem
          </h2>
          <div className="flex items-center gap-4 font-medium text-subtleText text-xs">
            <span className="flex items-center gap-1.5">
              <span className="h-3 w-3 rounded-sm bg-[#d5dbe6]" /> Previsto
            </span>
            <span className="flex items-center gap-1.5">
              <span className="h-3 w-3 rounded-sm bg-accent" /> Arrecadado
            </span>
          </div>
        </div>

        <PrevistoVsArrecadadoOrigem items={origensData} />
      </div>

      {/* Alerta de Vulnerabilidade Fiscal caso exista */}
      {rec.alerta_dependencia && (
        <AlertBox
          type="danger"
          title="Alerta: Alta Dependência de Transferências Externas"
        >
          A receita própria representa apenas {fmtPercent(rec.pct_propria)} do
          total arrecadado. O município apresenta elevada vulnerabilidade fiscal
          a repasses constitucionais federais e estaduais para manter o custeio
          público.
        </AlertBox>
      )}

      {/* Tabela Detalhada de Previsão vs Arrecadação */}
      <div className="pt-4">
        <DenseTable data={tableData} columns={tableCols} />
      </div>
    </div>
  );
}
