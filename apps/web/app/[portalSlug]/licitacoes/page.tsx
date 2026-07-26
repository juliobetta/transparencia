import {
  getAdesaoDeAta,
  getAnomaliasContratuais,
  getConcentracaoFornecedores,
  getLicitacaoGaps,
} from "@transparencia/db";
import {
  AlertBox,
  DenseTable,
  fmtCompact,
  KPICard,
  KPIGrid,
  SectionHeader,
} from "@transparencia/ui";

export const dynamic = "force-dynamic";

interface LicitacoesPageProps {
  params: Promise<{ portalSlug: string }>;
  searchParams: Promise<{ ano?: string; entidades?: string }>;
}

export default async function LicitacoesPage({
  params,
  searchParams,
}: LicitacoesPageProps) {
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

  const gaps = await getLicitacaoGaps(selectedYear, entidadesIds);
  const adesao = await getAdesaoDeAta(selectedYear, entidadesIds);
  const anomalias = await getAnomaliasContratuais(selectedYear, entidadesIds);
  const conc = await getConcentracaoFornecedores(selectedYear, entidadesIds);

  const acimaLimiteGaps = gaps.filter((g) => g.acimaLimite);

  const gapsCols = [
    { header: "Nº Contrato", accessorKey: "numero" as const },
    { header: "Fornecedor / Credor", accessorKey: "fornecedor" as const },
    { header: "Objeto", accessorKey: "objeto" as const },
    {
      header: "Valor (R$)",
      accessorKey: "valorContrato" as const,
      align: "right" as const,
      format: "currency" as const,
    },
    {
      header: "Limite Dispensa",
      accessorKey: "limiteDispensa" as const,
      align: "right" as const,
      format: "currency" as const,
    },
    {
      header: "Status",
      accessorKey: "acimaLimite" as const,
      align: "center" as const,
      format: "statusBadge" as const,
    },
  ];

  return (
    <div className="space-y-8">
      <div>
        <h1 className="font-bold font-serif text-3xl text-ink">
          Licitações & Contratos
        </h1>
        <p className="mt-1 text-sm text-subtleText">
          Monitoramento de contratações públicas, adesões a ata e fracionamento
          de despesa ({selectedYear}
          {isCurrentYear ? " · parcial" : ""})
        </p>
      </div>

      <KPIGrid columns={4}>
        <KPICard
          title="Sem Licitação Vinculada"
          value={gaps.length}
          subtext="Contratos sem nº de licitação"
          accent
        />
        <KPICard
          title="Contratos Acima do Limite"
          value={acimaLimiteGaps.length}
          subtext="Requerem auditoria"
          alert={acimaLimiteGaps.length > 0}
        />
        <KPICard
          title="Adesões a Ata de Registro"
          value={adesao.quantidade}
          subtext={`Valor: ${fmtCompact(adesao.valor)}`}
        />
        <KPICard
          title="Índice HHI (Concentração)"
          value={conc.hhi.toFixed(0)}
          subtext={
            conc.dominante ? `Dominante: ${conc.dominante}` : "Equilibrado"
          }
        />
      </KPIGrid>

      {acimaLimiteGaps.length > 0 && (
        <AlertBox type="danger" title="Alerta de Inconformidade Legal">
          Identificados <b>{acimaLimiteGaps.length} contratos sem licitação</b>{" "}
          cujo valor individual excede o limite legal de dispensa por valor.
        </AlertBox>
      )}

      {anomalias.fracionamento.length > 0 && (
        <AlertBox type="warning" title="Possível Fracionamento de Despesa">
          Encontrados <b>{anomalias.fracionamento.length} contratos</b> com o
          mesmo fornecedor em valores próximos ao limite de dispensa no mesmo
          período.
        </AlertBox>
      )}

      <div>
        <SectionHeader
          title="Contratos sem Licitação Vinculada"
          description="Relação completa de contratações diretas ou sem código de licitação informado"
        />
        <DenseTable
          data={gaps}
          columns={gapsCols}
          searchableKeys={["fornecedor", "objeto", "numero"]}
        />
      </div>
    </div>
  );
}
