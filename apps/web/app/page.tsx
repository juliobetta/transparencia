import { getPosicaoFiscal, getExecucaoOrcamentaria, summarizeExecucao, getLicitacaoGaps } from "@transparencia/db";
import { KPICard, KPIGrid, SectionHeader, AlertBox, DenseTable, fmtCompact, fmtCurrency, fmtPercent, Badge } from "@transparencia/ui";

export const dynamic = "force-dynamic";

export default async function VisaoGeralPage() {
  const currentYear = 2025;
  const posicao = await getPosicaoFiscal(currentYear);
  const execItems = await getExecucaoOrcamentaria(currentYear);
  const execSummary = summarizeExecucao(execItems);
  const gaps = await getLicitacaoGaps(currentYear);

  const credoresCols = [
    { header: "Fornecedor", accessorKey: "Fornecedor" as const },
    {
      header: "Pendente",
      accessorKey: "Pendente" as const,
      align: "right" as const,
      format: "currency" as const,
    },
  ];

  return (
    <div className="space-y-8">
      {/* Header */}
      <div>
        <h1 className="text-3xl font-bold font-serif text-ink">Visão Geral da Gestão Fiscal</h1>
        <p className="text-sm text-subtleText mt-1">
          Exercício de {currentYear} — Resumo executivo das contas públicas de Porciúncula/RJ
        </p>
      </div>

      {/* Grid de KPIs principais */}
      <KPIGrid columns={4}>
        <KPICard
          title="Receita Arrecadada"
          value={fmtCompact(posicao.total_arrecadado)}
          subtext="Total no exercício"
          accent
        />
        <KPICard
          title="Despesas Pagas"
          value={fmtCompact(posicao.total_saidas)}
          subtext="Correntes + Restos a pagar"
        />
        <KPICard
          title="Saldo Estimado"
          value={fmtCompact(posicao.saldo_estimado)}
          subtext="Arrecadado vs Saídas"
          trend={{
            value: posicao.saldo_estimado >= 0 ? "Superávit" : "Déficit",
            isPositive: posicao.saldo_estimado >= 0,
          }}
        />
        <KPICard
          title="Restos a Pagar Pendentes"
          value={fmtCompact(posicao.restos_pendentes_total)}
          subtext={`Adm. Anterior: ${fmtCompact(posicao.restos_pendentes_anteriores)}`}
          alert={posicao.restos_pendentes_anteriores > 0}
        />
      </KPIGrid>

      {/* Alerta de Restos a Pagar se houver pendência anterior */}
      {posicao.restos_pendentes_anteriores > 0 && (
        <AlertBox type="warning" title="Atenção: Passivo de Gestões Anteriores">
          O município possui <b>{fmtCurrency(posicao.restos_pendentes_anteriores)}</b> em restos a pagar
          pendentes referentes a exercícios anteriores a 2025.
        </AlertBox>
      )}

      {/* Execução Orçamentária Resumida */}
      <div>
        <SectionHeader
          title="Execução Orçamentária"
          description="Acompanhamento da dotação atualizada, empenhos e liquidações"
        />
        <KPIGrid columns={3}>
          <KPICard
            title="Dotação Atualizada"
            value={fmtCompact(execSummary.total_dotacao)}
            subtext="Orçamento total aprovado"
          />
          <KPICard
            title="Empenhado"
            value={fmtCompact(execSummary.total_empenhado)}
            subtext={`Taxa: ${fmtPercent(execSummary.total_dotacao > 0 ? (execSummary.total_empenhado / execSummary.total_dotacao) * 100 : 0)}`}
          />
          <KPICard
            title="Pago"
            value={fmtCompact(execSummary.total_pago)}
            subtext={`Taxa: ${fmtPercent(execSummary.total_empenhado > 0 ? (execSummary.total_pago / execSummary.total_empenhado) * 100 : 0)}`}
            accent
          />
        </KPIGrid>
      </div>

      {/* Credores Principais com Pendências */}
      {posicao.top_credores_adm_atual.length > 0 && (
        <div>
          <SectionHeader
            title="Maiores Credores da Gestão Atual"
            description="Principais fornecedores com restos a pagar acumulados a partir de 2025"
          />
          <DenseTable data={posicao.top_credores_adm_atual} columns={credoresCols} />
        </div>
      )}
    </div>
  );
}
