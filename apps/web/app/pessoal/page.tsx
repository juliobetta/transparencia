import {
  getExecucaoDecimoTerceiro,
  getFolhaVsServicos,
} from "@transparencia/db";
import {
  fmtCompact,
  fmtPercent,
  KPICard,
  KPIGrid,
  SectionHeader,
} from "@transparencia/ui";

export const dynamic = "force-dynamic";

export default async function PessoalPage() {
  const currentYear = 2025;
  const folhaData = await getFolhaVsServicos([currentYear]);
  const decimo13 = await getExecucaoDecimoTerceiro(currentYear);
  const row = folhaData[0] || {
    total_folha: 0,
    total_pago: 0,
    rcl_proxy: 0,
    percentual_folha: 0,
  };

  return (
    <div className="space-y-8">
      <div>
        <h1 className="font-bold font-serif text-3xl text-ink">
          Pessoal & Vencimentos
        </h1>
        <p className="mt-1 text-sm text-subtleText">
          Despesas com folha de pagamento, cargos e limites da Lei de
          Responsabilidade Fiscal ({currentYear})
        </p>
      </div>

      <KPIGrid columns={4}>
        <KPICard
          title="Total Folha de Pagamento"
          value={fmtCompact(row.total_folha)}
          subtext="Proventos brutos"
          accent
        />
        <KPICard
          title="Receita Corrente Líquida"
          value={fmtCompact(row.rcl_proxy)}
          subtext="Proxy RCL"
        />
        <KPICard
          title="Comprometimento LRF"
          value={fmtPercent(row.percentual_folha)}
          subtext="Limite Máximo LRF: 54.0%"
          alert={row.percentual_folha > 54}
        />
        <KPICard
          title="13º Salário Executado"
          value={decimo13 ? fmtCompact(decimo13.pago) : "N/D"}
          subtext={
            decimo13
              ? `Empenhado: ${fmtCompact(decimo13.empenhado)}`
              : "Sem dados"
          }
        />
      </KPIGrid>

      <div>
        <SectionHeader
          title="Indicadores da Lei de Responsabilidade Fiscal (LRF)"
          description="Comprometimento dos gastos com pessoal da Prefeitura de Porciúncula"
        />
        <div className="space-y-4 rounded-xl border border-borderLine bg-white p-6">
          <div className="flex justify-between font-semibold text-ink text-xs">
            <span>
              Comprometimento Atual: {fmtPercent(row.percentual_folha)}
            </span>
            <span>Limite Máximo LRF: 54.00%</span>
          </div>
          <div className="relative h-4 w-full overflow-hidden rounded-full bg-gray-100">
            <div
              className="h-full rounded-full transition-all duration-500"
              style={{
                width: `${Math.min(100, (row.percentual_folha / 54) * 100)}%`,
                backgroundColor:
                  row.percentual_folha > 54
                    ? "oklch(0.55 0.11 25)"
                    : "oklch(0.55 0.11 250)",
              }}
            />
          </div>
          <p className="text-subtleText text-xs">
            A LRF estabelece limite teto de 54% da Receita Corrente Líquida
            (RCL) para o Poder Executivo Municipal.
          </p>
        </div>
      </div>
    </div>
  );
}
