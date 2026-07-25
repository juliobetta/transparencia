import { getLicitacaoGaps, getAdesaoDeAta, getAnomaliasContratuais, getConcentracaoFornecedores } from "@transparencia/db";
import { KPICard, KPIGrid, SectionHeader, AlertBox, DenseTable, Badge, fmtCompact, fmtCurrency } from "@transparencia/ui";

export const revalidate = 60;

export default async function LicitacoesPage() {
  const currentYear = 2025;
  const gaps = await getLicitacaoGaps(currentYear);
  const adesao = await getAdesaoDeAta(currentYear);
  const anomalias = await getAnomaliasContratuais(currentYear);
  const conc = await getConcentracaoFornecedores(currentYear);

  const acimaLimiteGaps = gaps.filter((g) => g.acima_limite);

  const gapsCols = [
    { header: "Nº Contrato", accessorKey: "numero" as const },
    { header: "Fornecedor / Credor", accessorKey: "fornecedor" as const },
    { header: "Objeto", accessorKey: "objeto" as const },
    {
      header: "Valor (R$)",
      accessorKey: "valor_contrato" as const,
      align: "right" as const,
      format: "currency" as const,
    },
    {
      header: "Limite Dispensa",
      accessorKey: "limite_dispensa" as const,
      align: "right" as const,
      format: "currency" as const,
    },
    {
      header: "Status",
      accessorKey: "acima_limite" as const,
      align: "center" as const,
      format: "statusBadge" as const,
    },
  ];

  return (
    <div className="space-y-8">
      <div>
        <h1 className="text-3xl font-bold font-serif text-ink">Licitações & Contratos</h1>
        <p className="text-sm text-subtleText mt-1">
          Monitoramento de contratações públicas, adespões a ata e fracionamento de despesa ({currentYear})
        </p>
      </div>

      <KPIGrid columns={4}>
        <KPICard title="Sem Licitação Vinculada" value={gaps.length} subtext="Contratos sem nº de licitação" accent />
        <KPICard title="Contratos Acima do Limite" value={acimaLimiteGaps.length} subtext="Requerem auditoria" alert={acimaLimiteGaps.length > 0} />
        <KPICard title="Adesões a Ata de Registro" value={adesao.quantidade} subtext={`Valor: ${fmtCompact(adesao.valor)}`} />
        <KPICard title="Índice HHI (Concentração)" value={conc.hhi.toFixed(0)} subtext={conc.dominante ? `Dominante: ${conc.dominante}` : "Equilibrado"} />
      </KPIGrid>

      {acimaLimiteGaps.length > 0 && (
        <AlertBox type="danger" title="Alerta de Inconformidade Legal">
          Identificados <b>{acimaLimiteGaps.length} contratos sem licitação</b> cujo valor individual excede o limite legal de dispensa por valor.
        </AlertBox>
      )}

      {anomalias.fracionamento.length > 0 && (
        <AlertBox type="warning" title="Possível Fracionamento de Despesa">
          Encontrados <b>{anomalias.fracionamento.length} contratos</b> com o mesmo fornecedor em valores próximos ao limite de dispensa no mesmo período.
        </AlertBox>
      )}

      <div>
        <SectionHeader
          title="Contratos sem Licitação Vinculada"
          description="Relação completa de contratações diretas ou sem código de licitação informado"
        />
        <DenseTable data={gaps} columns={gapsCols} searchableKeys={["fornecedor", "objeto", "numero"]} />
      </div>
    </div>
  );
}
