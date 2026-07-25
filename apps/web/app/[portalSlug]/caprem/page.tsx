import { getHistoriaCaprem } from "@transparencia/db";
import {
  DenseTable,
  fmtCompact,
  KPICard,
  KPIGrid,
  SectionHeader,
} from "@transparencia/ui";

export const dynamic = "force-dynamic";

interface CapremPageProps {
  params: Promise<{ portalSlug: string }>;
  searchParams: Promise<{ ano?: string; entidades?: string }>;
}

export default async function CapremPage({
  params,
  searchParams,
}: CapremPageProps) {
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

  const caprem = await getHistoriaCaprem(selectedYear, entidadesIds);

  const entidadesCols = [
    { header: "Entidade / Órgão", accessorKey: "entidade" as const },
    {
      header: "Empenhado (R$)",
      accessorKey: "empenhado" as const,
      align: "right" as const,
      format: "currency" as const,
    },
    {
      header: "Liquidado (R$)",
      accessorKey: "liquidado" as const,
      align: "right" as const,
      format: "currency" as const,
    },
    {
      header: "Pago (R$)",
      accessorKey: "pago" as const,
      align: "right" as const,
      format: "currency" as const,
    },
  ];

  return (
    <div className="space-y-8">
      <div>
        <h1 className="font-bold font-serif text-3xl text-ink">
          Painel CAPREM
        </h1>
        <p className="mt-1 text-sm text-subtleText">
          Acompanhamento dos repasses previdenciários e obrigações com a Caixa
          de Aposentadoria e Pensões ({selectedYear}
          {isCurrentYear ? " · parcial" : ""})
        </p>
      </div>

      <KPIGrid columns={3}>
        <KPICard
          title="Total Empenhado"
          value={fmtCompact(caprem.total_empenhado)}
          subtext="Compromissos previdenciários"
          accent
        />
        <KPICard
          title="Total Liquidado"
          value={fmtCompact(caprem.total_liquidado)}
          subtext="Atestado pelos órgãos"
        />
        <KPICard
          title="Total Repassado/Pago"
          value={fmtCompact(caprem.total_pago)}
          subtext="Efetivamente transferido"
        />
      </KPIGrid>

      <div>
        <SectionHeader
          title="Repasses por Entidade ao CAPREM"
          description="Valores empenhados e repassados por órgão da administração municipal ao regime de previdência"
        />
        <DenseTable
          data={caprem.entidades}
          columns={entidadesCols}
          searchableKeys={["entidade"]}
        />
      </div>
    </div>
  );
}
