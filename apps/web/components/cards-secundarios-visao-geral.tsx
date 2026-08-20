import { cn, Tooltip } from "@transparencia/ui";
import { CircleQuestionMarkIcon } from "lucide-react";
import Link from "next/link";

export interface AntiguidadeBarItem {
  year: string;
  amountFormatted?: string;
  percentage: number;
  colorClass?: string;
}

export interface DespesasCardData {
  title?: string;
  linkText?: string;
  linkHref?: string;
  totalRestosPagarFormatted?: string;
  subtext?: string;
  antiguidadeBars?: AntiguidadeBarItem[];
  footerText?: string;
}

export interface LicitacaoItemData {
  count: number | string;
  label: string;
  isAlert?: boolean;
}

export interface LicitacoesCardData {
  title?: string;
  linkText?: string;
  linkHref?: string;
  items?: LicitacaoItemData[];
}

export interface PessoalCardData {
  title?: string;
  linkText?: string;
  linkHref?: string;
  receitaFolhaPercentFormatted?: string;
  receitaFolhaPercentValue?: number;
  subtext?: string;
  lrfLimitPercentValue?: number;
  lrfLimitPercentFormatted?: string;
  footerText?: string;
}

export interface CardsSecundariosVisaoGeralProps {
  despesas?: DespesasCardData;
  licitacoes?: LicitacoesCardData;
  pessoal?: PessoalCardData;
  className?: string;
}

export function CardsSecundariosVisaoGeral({
  despesas,
  licitacoes,
  pessoal,
  className,
}: CardsSecundariosVisaoGeralProps) {
  const despesasTitle = despesas?.title ?? "Despesas";
  const despesasLinkText = despesas?.linkText ?? "Restos a pagar →";
  const despesasLinkHref = despesas?.linkHref ?? "/despesas";
  const despesasTotal = despesas?.totalRestosPagarFormatted;
  const despesasSubtext = despesas?.subtext;
  const despesasBars = despesas?.antiguidadeBars ?? [];
  const despesasFooter = despesas?.footerText;

  const licitacoesTitle = licitacoes?.title ?? "Licitações";
  const licitacoesLinkText = licitacoes?.linkText ?? "Contratos →";
  const licitacoesLinkHref = licitacoes?.linkHref ?? "/licitacoes";
  const licitacoesItems = licitacoes?.items ?? [];

  const pessoalTitle = pessoal?.title ?? "Pessoal";
  const pessoalLinkText = pessoal?.linkText ?? "Folha →";
  const pessoalLinkHref = pessoal?.linkHref ?? "/pessoal";
  const pessoalPercentFormatted = pessoal?.receitaFolhaPercentFormatted;
  const pessoalPercentVal = pessoal?.receitaFolhaPercentValue ?? 0;
  const pessoalSubtext = pessoal?.subtext;
  const lrfLimitVal = pessoal?.lrfLimitPercentValue ?? 54;
  const lrfLimitFormatted =
    pessoal?.lrfLimitPercentFormatted ?? `${lrfLimitVal}% LRF`;
  const pessoalFooter = pessoal?.footerText;

  return (
    <div className={cn("grid grid-cols-1 gap-4 md:grid-cols-3", className)}>
      {/* Card 1: Despesas */}
      <div className="flex flex-col justify-between rounded-[14px] border border-[#e7e9ee] bg-white p-5 shadow-sm">
        <div>
          {/* Cabeçalho */}
          <div className="flex items-center justify-between border-[#f4f5f7] border-b pb-3">
            <div className="flex items-center gap-1.5">
              <span className="font-bold font-serif text-base text-ink">
                {despesasTitle}
              </span>
              <Tooltip
                ariaLabel="Informações sobre Restos a Pagar Processados e Não Processados"
                position="bottom"
                content={
                  <div>
                    <span className="mb-1.5 block font-semibold text-sky-400 text-xs">
                      Restos a Pagar (Norma STN/MCASP)
                    </span>
                    <p className="mb-1 text-[11px] text-slate-300 leading-snug">
                      • <strong>Processados:</strong> Dívidas de serviços já
                      prestados e liquidados com direito adquirido do credor.
                    </p>
                    <p className="text-[11px] text-slate-300 leading-snug">
                      • <strong>Não Processados:</strong> Obras ou contratos em
                      andamento pendentes de medição e liquidação.
                    </p>
                  </div>
                }
              >
                <CircleQuestionMarkIcon className="h-4 w-4 text-slate-400" />
              </Tooltip>
            </div>
            {despesasLinkHref && (
              <Link
                href={despesasLinkHref}
                className="font-medium text-subtleText text-xs transition-colors hover:text-accent"
              >
                {despesasLinkText}
              </Link>
            )}
          </div>

          {/* Destaque Numérico */}
          <div className="my-4">
            {despesasTotal ? (
              <div className="font-bold font-serif text-2xl text-[oklch(0.55_0.11_25)] leading-none tracking-tight sm:text-3xl">
                {despesasTotal}
              </div>
            ) : (
              <div className="text-subtleText text-xs italic">
                Sem restos a pagar registrados
              </div>
            )}
            {despesasSubtext && (
              <div className="mt-1.5 font-medium text-subtleText text-xs">
                {despesasSubtext}
              </div>
            )}
          </div>

          {/* Antiguidade Bars */}
          {despesasBars.length > 0 && (
            <div className="my-3 flex h-10 items-end gap-1.5">
              {despesasBars.map((bar, idx) => {
                const colorClass =
                  bar.colorClass ||
                  (idx === despesasBars.length - 1
                    ? "bg-[oklch(0.55_0.11_25)]"
                    : "bg-[#f0dadd]");
                return (
                  <div
                    key={bar.year}
                    className="group relative flex h-full flex-1 flex-col items-center justify-end"
                  >
                    <div
                      className={cn(
                        "w-full rounded-sm transition-all duration-300",
                        colorClass,
                      )}
                      style={{
                        height: `${Math.min(100, Math.max(10, bar.percentage))}%`,
                      }}
                    />
                    <span className="mt-1 font-mono text-[9px] text-mutedText">
                      {bar.year}
                    </span>
                  </div>
                );
              })}
            </div>
          )}
        </div>

        {/* Rodapé */}
        {despesasFooter && (
          <div className="mt-2 border-[#f4f5f7] border-t pt-2.5 font-medium text-[11px] text-subtleText">
            {despesasFooter}
          </div>
        )}
      </div>

      {/* Card 2: Licitações */}
      <div className="flex flex-col justify-between rounded-[14px] border border-[#e7e9ee] bg-white p-5 shadow-sm">
        <div>
          {/* Cabeçalho */}
          <div className="flex items-center justify-between border-[#f4f5f7] border-b pb-3">
            <span className="font-bold font-serif text-base text-ink">
              {licitacoesTitle}
            </span>
            {licitacoesLinkHref && (
              <Link
                href={licitacoesLinkHref}
                className="font-medium text-subtleText text-xs transition-colors hover:text-accent"
              >
                {licitacoesLinkText}
              </Link>
            )}
          </div>

          {/* Lista de Itens */}
          <div className="my-3.5 space-y-2.5">
            {licitacoesItems.length > 0 ? (
              licitacoesItems.map((item) => (
                <div
                  key={item.label}
                  className="flex items-center gap-2 text-xs"
                >
                  <strong
                    className={cn(
                      "w-7 shrink-0 font-bold font-serif text-base",
                      item.isAlert ? "text-[oklch(0.55_0.11_25)]" : "text-ink",
                    )}
                  >
                    {item.count}
                  </strong>
                  <span className="flex-1 truncate font-medium text-subtleText">
                    {item.label}
                  </span>
                </div>
              ))
            ) : (
              <div className="py-4 text-center text-subtleText text-xs italic">
                Nenhum indicador registrado
              </div>
            )}
          </div>
        </div>
      </div>

      {/* Card 3: Pessoal */}
      <div className="flex flex-col justify-between rounded-[14px] border border-[#e7e9ee] bg-white p-5 shadow-sm">
        <div>
          {/* Cabeçalho */}
          <div className="flex items-center justify-between border-[#f4f5f7] border-b pb-3">
            <span className="font-bold font-serif text-base text-ink">
              {pessoalTitle}
            </span>
            {pessoalLinkHref && (
              <Link
                href={pessoalLinkHref}
                className="font-medium text-subtleText text-xs transition-colors hover:text-accent"
              >
                {pessoalLinkText}
              </Link>
            )}
          </div>

          {/* Destaque Numérico */}
          <div className="my-4">
            {pessoalPercentFormatted ? (
              <div className="font-bold font-serif text-2xl text-ink leading-none tracking-tight sm:text-3xl">
                {pessoalPercentFormatted}
              </div>
            ) : (
              <div className="text-subtleText text-xs italic">
                Sem dados de folha registrados
              </div>
            )}
            {pessoalSubtext && (
              <div className="mt-1.5 font-medium text-subtleText text-xs">
                {pessoalSubtext}
              </div>
            )}
          </div>

          {/* Barra de Progresso + Marcador LRF */}
          {pessoalPercentFormatted && (
            <div className="my-3 space-y-1.5">
              <div className="relative h-2.5 w-full overflow-visible rounded-md bg-[#f4f5f7]">
                {/* Progresso da Folha */}
                <div
                  className="h-full rounded-md bg-sky-600 transition-all duration-500"
                  style={{
                    width: `${Math.min(100, Math.max(0, pessoalPercentVal))}%`,
                  }}
                />
                {/* Linha Vermelha de Limite LRF */}
                <div
                  className="absolute top-[-3px] z-10 h-4 w-0.5 bg-red-600"
                  style={{
                    left: `${Math.min(100, Math.max(0, lrfLimitVal))}%`,
                  }}
                  title={`Limite LRF: ${lrfLimitFormatted}`}
                />
              </div>
              <div className="flex items-center justify-between font-medium text-[10.5px] text-mutedText">
                <span>{pessoalPercentVal}% atual</span>
                <span className="font-semibold text-red-700">
                  limite LRF: {lrfLimitFormatted}
                </span>
              </div>
            </div>
          )}
        </div>

        {/* Rodapé */}
        {pessoalFooter && (
          <div className="mt-2 border-[#f4f5f7] border-t pt-2.5 font-medium text-[11px] text-subtleText">
            {pessoalFooter}
          </div>
        )}
      </div>
    </div>
  );
}
