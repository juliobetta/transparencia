"use client";

import type { ContratoServicoVigente } from "@transparencia/db";
import { type Column, DenseTable, fmtDate } from "@transparencia/ui";
import { useMemo } from "react";
import { ContratoServicoVigenteCard } from "./contrato-servico-vigente-card";

interface ContratosServicosVigentesSectionProps {
  contratos: ContratoServicoVigente[];
}

export function ContratosServicosVigentesSection({
  contratos,
}: ContratosServicosVigentesSectionProps) {
  const tableData = useMemo(() => {
    if (!Array.isArray(contratos)) return [];
    return contratos.map((c) => ({
      ...c,
      vigenciaFormatada: c.vencimentoAtual
        ? `${fmtDate(c.dataInicio)} – ${fmtDate(c.vencimentoAtual)}`
        : c.dataInicio
          ? `A partir de ${fmtDate(c.dataInicio)}`
          : "Em vigência",
    }));
  }, [contratos]);

  if (!contratos || contratos.length === 0) {
    return null;
  }

  const top3 = contratos.slice(0, 3);

  const columns: Column<(typeof tableData)[number]>[] = [
    {
      header: "Fornecedor",
      accessorKey: "fornecedorNome",
      sortable: true,
      className: "min-w-[180px] max-w-[220px]",
    },
    {
      header: "Objeto",
      accessorKey: "objetoDescricao",
      sortable: true,
      className: "min-w-[220px] max-w-[300px] truncate",
    },
    {
      header: "Vigência",
      accessorKey: "vigenciaFormatada",
      sortable: true,
      align: "center",
      className: "whitespace-nowrap font-medium text-slate-600",
    },
    {
      header: "Empenhado",
      accessorKey: "totalEmpenhado",
      format: "currency",
      align: "right",
      sortable: true,
      isSerifNumeric: true,
    },
    {
      header: "Liquidado",
      accessorKey: "totalLiquidado",
      format: "currency",
      align: "right",
      sortable: true,
      isSerifNumeric: true,
    },
    {
      header: "Pago",
      accessorKey: "totalPago",
      format: "currency",
      align: "right",
      sortable: true,
      isSerifNumeric: true,
    },
    {
      header: "Saldo Pendente",
      accessorKey: "saldoPendente",
      format: "currency",
      align: "right",
      sortable: true,
      isSerifNumeric: true,
    },
    {
      header: "% Pago",
      accessorKey: "percentualPago",
      format: "percent",
      align: "right",
      sortable: true,
      isSerifNumeric: true,
    },
  ];

  return (
    <section className="space-y-6">
      {/* Header */}
      <div className="flex flex-col justify-between gap-1 border-ink border-t-2 pt-8 sm:flex-row sm:items-baseline">
        <div>
          <h2 className="font-bold font-serif text-ink text-xl tracking-tight">
            Contratos de Serviços Vigentes
          </h2>
          <p className="text-slate-600 text-xs leading-relaxed sm:text-sm">
            Principais contratos de serviços de terceiros em execução, ordenados
            pelo menor valor pago e maior saldo pendente para evidenciar
            potenciais exposições fiscais.
          </p>
        </div>
        <span className="shrink-0 rounded-full border border-borderLine bg-gray-100 px-2.5 py-1 font-medium text-subtleText text-xs">
          {contratos.length} {contratos.length === 1 ? "contrato" : "contratos"}{" "}
          em vigência
        </span>
      </div>

      {/* Top 3 Cards Grid */}
      <div className="grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-3">
        {top3.map((c, idx) => (
          <ContratoServicoVigenteCard
            key={
              c.contratoServicoId ||
              `${c.fornecedorNome}-${c.fornecedorCnpj}-${idx}`
            }
            contrato={c}
          />
        ))}
      </div>

      {/* Tabela Completa via DenseTable (busca, ordenacao, paginacao, csv) */}
      <DenseTable
        data={tableData}
        columns={columns}
        searchPlaceholder="Buscar por fornecedor, CNPJ ou objeto..."
        searchableKeys={["fornecedorNome", "fornecedorCnpj", "objetoDescricao"]}
        pageSize={10}
        sortable={true}
        enableExportCsv={true}
        exportFilename="contratos_servicos_vigentes.csv"
        rowKey="contratoServicoId"
      />
    </section>
  );
}
