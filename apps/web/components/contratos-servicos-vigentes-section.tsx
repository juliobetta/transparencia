"use client";

import type { ContratoServicoVigente } from "@transparencia/db";
import { type Column, DenseTable, fmtDate } from "@transparencia/ui";
import { useMemo, useState } from "react";
import { ContratoServicoVigenteCard } from "./contrato-servico-vigente-card";

interface ContratosServicosVigentesSectionProps {
  contratos: ContratoServicoVigente[];
}

type FilterStatus = "em_execucao" | "concluido" | "inexecutado" | "todos";

export function ContratosServicosVigentesSection({
  contratos,
}: ContratosServicosVigentesSectionProps) {
  const [statusFilter, setStatusFilter] = useState<FilterStatus>("em_execucao");

  const counts = useMemo(() => {
    if (!Array.isArray(contratos)) {
      return { em_execucao: 0, concluido: 0, inexecutado: 0, todos: 0 };
    }
    const res = {
      em_execucao: 0,
      concluido: 0,
      inexecutado: 0,
      todos: contratos.length,
    };
    for (const c of contratos) {
      const st = c.statusExecucao || "em_execucao";
      if (st in res) {
        res[st as keyof typeof res]++;
      }
    }
    return res;
  }, [contratos]);

  const filteredContratos = useMemo(() => {
    if (!Array.isArray(contratos)) return [];
    if (statusFilter === "todos") return contratos;
    return contratos.filter(
      (c) => (c.statusExecucao || "em_execucao") === statusFilter,
    );
  }, [contratos, statusFilter]);

  const tableData = useMemo(() => {
    if (!Array.isArray(filteredContratos)) return [];
    return filteredContratos.map((c) => ({
      ...c,
      statusLabel:
        c.statusExecucao === "inexecutado"
          ? "Não Executado"
          : c.statusExecucao === "concluido"
            ? "Concluído"
            : "Em Execução",
      vigenciaFormatada: (() => {
        if (c.dataInicio && c.vencimentoAtual) {
          return `${fmtDate(c.dataInicio)} – ${fmtDate(c.vencimentoAtual)}`;
        }
        if (c.vencimentoAtual) {
          return `Até ${fmtDate(c.vencimentoAtual)}`;
        }
        if (c.dataInicio) {
          return `A partir de ${fmtDate(c.dataInicio)}`;
        }
        return "";
      })(),
    }));
  }, [filteredContratos]);

  if (!contratos || contratos.length === 0) {
    return null;
  }

  const top3 = filteredContratos.slice(0, 3);

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
      header: "Status",
      accessorKey: "statusLabel",
      sortable: true,
      align: "center",
      className: "whitespace-nowrap font-medium text-slate-700 text-xs",
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
          {filteredContratos.length} de {contratos.length}{" "}
          {contratos.length === 1 ? "contrato" : "contratos"}
        </span>
      </div>

      {/* Segmented Filter Pills */}
      <div className="flex flex-wrap items-center gap-2 border-slate-200/80 border-b pb-3">
        <span className="font-semibold text-slate-700 text-xs">
          Status de Execução:
        </span>
        <button
          type="button"
          onClick={() => setStatusFilter("em_execucao")}
          className={`rounded-lg px-3 py-1 font-medium text-xs transition-colors ${
            statusFilter === "em_execucao"
              ? "bg-blue-600 text-white shadow-xs"
              : "bg-slate-100 text-slate-700 hover:bg-slate-200"
          }`}
        >
          Em Execução ({counts.em_execucao})
        </button>
        <button
          type="button"
          onClick={() => setStatusFilter("concluido")}
          className={`rounded-lg px-3 py-1 font-medium text-xs transition-colors ${
            statusFilter === "concluido"
              ? "bg-blue-600 text-white shadow-xs"
              : "bg-slate-100 text-slate-700 hover:bg-slate-200"
          }`}
        >
          Concluídos ({counts.concluido})
        </button>
        <button
          type="button"
          onClick={() => setStatusFilter("inexecutado")}
          className={`rounded-lg px-3 py-1 font-medium text-xs transition-colors ${
            statusFilter === "inexecutado"
              ? "bg-blue-600 text-white shadow-xs"
              : "bg-slate-100 text-slate-700 hover:bg-slate-200"
          }`}
        >
          Não Executados ({counts.inexecutado})
        </button>
        <button
          type="button"
          onClick={() => setStatusFilter("todos")}
          className={`rounded-lg px-3 py-1 font-medium text-xs transition-colors ${
            statusFilter === "todos"
              ? "bg-blue-600 text-white shadow-xs"
              : "bg-slate-100 text-slate-700 hover:bg-slate-200"
          }`}
        >
          Todos ({counts.todos})
        </button>
      </div>

      {/* Top 3 Cards Grid */}
      {top3.length > 0 ? (
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
      ) : (
        <div className="rounded-xl border border-slate-300 border-dashed p-6 text-center text-slate-500 text-sm">
          Nenhum contrato encontrado para a visão "{statusFilter}".
        </div>
      )}

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
