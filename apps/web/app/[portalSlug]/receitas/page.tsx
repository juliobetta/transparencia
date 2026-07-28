import { getFontesReceita, getPortalConfig } from "@transparencia/db";
import {
  AlertBox,
  CarrosChefeArrecadacao,
  DenseTable,
  EmendasCard,
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
    receitaPropria: 0,
    transferenciasUniao: 0,
    transferenciasEstado: 0,
    total: 0,
    pctPropria: 0,
    pctPropriaPrevisto: 0,
    alertaDependencia: false,
    receitaPropriaPrevisto: 0,
    receitaPropriaArrecadado: 0,
    transferenciasUniaoPrevisto: 0,
    transferenciasUniaoArrecadado: 0,
    transferenciasEstadoPrevisto: 0,
    transferenciasEstadoArrecadado: 0,
    totalPrevisto: 0,
    totalArrecadado: 0,
    pctArrecadado: 0,
    totalPctChange: null,
    emendasTotalArrecadado: 0,
    emendasPixArrecadado: 0,
    emendasIndividuaisArrecadado: 0,
    fpmArrecadado: 0,
    icmsArrecadado: 0,
    issIptuArrecadado: 0,
  };

  const totalArr = rec.totalArrecadado;
  const totalPrev = rec.totalPrevisto;
  const pctArrecadadoAnual = (rec.pctArrecadado || 0) * 100;

  const partialPeriod = getPartialYearPeriod();

  const origensData = [
    {
      fonte: "Transferências da União",
      previsto: rec.transferenciasUniaoPrevisto,
      arrecadado: rec.transferenciasUniaoArrecadado,
      pctRealizado:
        rec.transferenciasUniaoPrevisto > 0
          ? (rec.transferenciasUniaoArrecadado /
              rec.transferenciasUniaoPrevisto) *
            100
          : 0,
    },
    {
      fonte: "Transferências do Estado",
      previsto: rec.transferenciasEstadoPrevisto,
      arrecadado: rec.transferenciasEstadoArrecadado,
      pctRealizado:
        rec.transferenciasEstadoPrevisto > 0
          ? (rec.transferenciasEstadoArrecadado /
              rec.transferenciasEstadoPrevisto) *
            100
          : 0,
    },
    {
      fonte: "Receita própria",
      previsto: rec.receitaPropriaPrevisto,
      arrecadado: rec.receitaPropriaArrecadado,
      pctRealizado:
        rec.receitaPropriaPrevisto > 0
          ? (rec.receitaPropriaArrecadado / rec.receitaPropriaPrevisto) * 100
          : 0,
    },
  ];

  const tableData = [
    {
      fonte: "Receita Própria (Municipal)",
      previsto: rec.receitaPropriaPrevisto,
      arrecadado: rec.receitaPropriaArrecadado,
      pct:
        rec.receitaPropriaPrevisto > 0
          ? (rec.receitaPropriaArrecadado / rec.receitaPropriaPrevisto) * 100
          : 0,
    },
    {
      fonte: "Transferências da União",
      previsto: rec.transferenciasUniaoPrevisto,
      arrecadado: rec.transferenciasUniaoArrecadado,
      pct:
        rec.transferenciasUniaoPrevisto > 0
          ? (rec.transferenciasUniaoArrecadado /
              rec.transferenciasUniaoPrevisto) *
            100
          : 0,
    },
    {
      fonte: "Transferências do Estado",
      previsto: rec.transferenciasEstadoPrevisto,
      arrecadado: rec.transferenciasEstadoArrecadado,
      pct:
        rec.transferenciasEstadoPrevisto > 0
          ? (rec.transferenciasEstadoArrecadado /
              rec.transferenciasEstadoPrevisto) *
            100
          : 0,
    },
    {
      fonte: "Total Orçamentário",
      previsto: rec.totalPrevisto,
      arrecadado: rec.totalArrecadado,
      pct:
        rec.totalPrevisto > 0
          ? (rec.totalArrecadado / rec.totalPrevisto) * 100
          : 0,
      className: "font-semibold bg-gray-200",
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
    rec.totalPctChange != null
      ? rec.totalPctChange >= 0
        ? `▲ ${rec.totalPctChange.toFixed(1).replace(".", ",")}% vs. ${selectedYear - 1}`
        : `▼ ${Math.abs(rec.totalPctChange).toFixed(1).replace(".", ",")}% vs. ${selectedYear - 1}`
      : "Orçamento aprovado";

  return (
    <div className="space-y-6">
      {/* Eyebrow + Título + Subtítulo */}
      <div>
        <span className="inline-block font-semibold text-accent text-xs uppercase tracking-wider">
          ADMINISTRATIVO · EXERCÍCIO {selectedYear}
          {isCurrentYear ? ` (PARCIAL, ${partialPeriod})` : ""}
        </span>
        <h1 className="font-bold font-serif text-3xl text-slate-900">
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
        <div className="h-3.5 w-full overflow-hidden rounded-md bg-[#eef0f4]">
          <div
            className="h-full rounded-md bg-accent transition-all duration-500"
            style={{
              width: `${Math.min(100, Math.max(0, pctArrecadadoAnual))}%`,
            }}
          />
        </div>
      </div>

      {/* Destaque de Emendas Parlamentares */}
      <EmendasCard
        totalEmendas={rec.emendasTotalArrecadado || 0}
        pctDoArrecadado={
          totalArr > 0 ? (rec.emendasTotalArrecadado / totalArr) * 100 : 0
        }
        emendasPix={rec.emendasPixArrecadado || 0}
        emendasIndividuais={rec.emendasIndividuaisArrecadado || 0}
      />

      {/* Previsto vs. Arrecadado por Origem */}
      <div className="space-y-3 border-[#1a1d21] border-t-2 pt-3">
        <div className="flex flex-col gap-1 md:flex-row md:items-baseline md:justify-between">
          <h2 className="font-bold font-serif text-ink text-xl">
            Previsto vs. arrecadado por origem
          </h2>
          <div className="flex items-center gap-4 font-medium text-subtleText text-xs">
            <span className="flex items-center gap-1.5">
              <span className="h-3 w-3 rounded-sm bg-[#3775b3]" /> Arrecadado
            </span>
            <span className="flex items-center gap-1.5">
              <span className="h-3 w-3 rounded-sm border border-[#c4cbd8] bg-[#eef0f4]" />{" "}
              Previsto (meta LOA)
            </span>
          </div>
        </div>
        <p className="text-subtleText text-xs">
          O comprimento da barra é o valor previsto — mesma régua de R$ para
          todas as origens, então os tamanhos são comparáveis. A parte cheia é o
          que já entrou no caixa.
        </p>

        <PrevistoVsArrecadadoOrigem items={origensData} />
      </div>

      {/* Os 3 carros-chefe da arrecadação */}
      <CarrosChefeArrecadacao
        fpm={rec.fpmArrecadado || 0}
        icms={rec.icmsArrecadado || 0}
        issIptu={rec.issIptuArrecadado || 0}
        totalArrecadado={totalArr}
      />

      {/* Tabela Detalhada de Previsão vs Arrecadação */}
      <div className="pt-4">
        <DenseTable data={tableData} columns={tableCols} />
      </div>

      {/* Alerta de Vulnerabilidade Fiscal caso exista */}
      {rec.alertaDependencia && (
        <AlertBox
          type="danger"
          title="Alerta: Alta Dependência de Transferências Externas"
        >
          A receita própria representa apenas {fmtPercent(rec.pctPropria)} do
          total arrecadado. O município apresenta elevada vulnerabilidade fiscal
          a repasses constitucionais federais e estaduais para manter o custeio
          público.
        </AlertBox>
      )}
    </div>
  );
}
