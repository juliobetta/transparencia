"use client";

import {
  Bot,
  ChevronDown,
  ChevronRight,
  ChevronUp,
  Database,
  Download,
  Info,
  Loader2,
  RotateCcw,
  Send,
  Sparkles,
  Square,
  ThumbsDown,
  ThumbsUp,
  X,
} from "lucide-react";
import { usePathname } from "next/navigation";
import posthog from "posthog-js";
import { useEffect, useRef, useState } from "react";
import { createPortal } from "react-dom";
import type { AssistantResponse } from "../api/assistant/chat/route";
import {
  AssistantProvider,
  type ChatMessage,
  useAssistantContext,
} from "./assistant-context";

export const ROUTE_SUGGESTED_QUESTIONS: Record<string, string[]> = {
  "/saude": [
    "Qual o total gasto com Saúde no exercício?",
    "Quais as receitas de repasse do SUS/União e Estado?",
    "Quanto foi investido em emendas parlamentares na saúde?",
  ],
  "/caprem": [
    "Qual a arrecadação e despesa previdenciária do CAPREM?",
    "Qual o saldo atuarial e aportes da prefeitura ao CAPREM?",
    "Quanto foi pago em aposentadorias e pensões?",
  ],
  "/licitacoes": [
    "Qual o total de contratos celebrados e vigentes?",
    "Qual o volume em dispensas e inexigibilidades de licitação?",
    "Quais são os maiores fornecedores do município?",
  ],
  "/pessoal": [
    "Qual o total gasto com folha de pagamento e pessoal?",
    "Qual o percentual de cargos em comissão ocupados por efetivos?",
    "Quanto foi despendido com 13º salário e encargos?",
  ],
  "/receitas": [
    "Qual a receita total arrecadada no município?",
    "Qual a proporção entre receita própria e transferências?",
    "Quanto foi arrecadado em receitas extra-orçamentárias?",
  ],
  "/despesas": [
    "Quais os maiores órgãos e unidades orçamentárias em gastos?",
    "Qual o total de restos a pagar pagos no exercício?",
    "Quanto foi empenhado, liquidado e pago no total?",
  ],
  "/orcamento": [
    "Qual o orçamento aprovado e atualizado para o ano?",
    "Quais funções contábeis receberam maior fatia orçamentária?",
    "Qual o percentual de execução do orçamento municipal?",
  ],
  default: [
    "Qual a receita arrecadada este ano?",
    "Quanto foi gasto com a Saúde?",
    "Quais os aportes para o CAPREM?",
    "Qual o total em dispensas de licitação?",
  ],
};

interface AssistantChatDrawerProps {
  portalSlug?: string;
  ano?: string;
}

function FormattedMarkdown({ text }: { text?: string }) {
  if (!text) return null;

  const parts = text.split(/(\*\*[^*]+\*\*|\*[^*]+\*)/g);

  return (
    <span>
      {parts.map((part, i) => {
        const key = `part-${i}-${part.slice(0, 5)}`;
        if (part.startsWith("**") && part.endsWith("**")) {
          return (
            <strong key={key} className="font-semibold text-slate-900">
              {part.slice(2, -2)}
            </strong>
          );
        }
        if (part.startsWith("*") && part.endsWith("*")) {
          return <em key={key}>{part.slice(1, -1)}</em>;
        }
        return part;
      })}
    </span>
  );
}

function AssistantChatDrawerContent({
  portalSlug = "porciuncula_prefeitura",
  ano = "2025",
}: AssistantChatDrawerProps) {
  const { state, dispatch, resetConversation } = useAssistantContext();
  const [mounted, setMounted] = useState(false);
  const pathname = usePathname();
  const isProduction = process.env.NODE_ENV === "production";

  const messagesEndRef = useRef<HTMLDivElement>(null);
  const abortControllerRef = useRef<AbortController | null>(null);

  // Determinar sugestões dinâmicas por rota
  const activeSuggestedQuestions = (() => {
    if (!pathname) return ROUTE_SUGGESTED_QUESTIONS.default;
    for (const routeKey of Object.keys(ROUTE_SUGGESTED_QUESTIONS)) {
      if (routeKey !== "default" && pathname.includes(routeKey)) {
        return ROUTE_SUGGESTED_QUESTIONS[routeKey];
      }
    }
    return ROUTE_SUGGESTED_QUESTIONS.default;
  })();

  useEffect(() => {
    setMounted(true);
  }, []);

  // biome-ignore lint/correctness/useExhaustiveDependencies: scroll no update
  useEffect(() => {
    if (state.isOpen) {
      messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
    }
  }, [state.messages.length, state.isLoading, state.isOpen]);

  const handleFeedback = (msgId: string, text: string, score: 1 | -1) => {
    dispatch({
      type: "SET_FEEDBACK_FOR",
      payload: { messageId: msgId, score },
    });
    try {
      posthog.capture("ai_feedback", {
        score,
        message_id: msgId,
        answer_snippet: text.slice(0, 300),
        portal_slug: portalSlug,
        ano,
      });
    } catch (_err) {}
  };

  const handleCancelRequest = () => {
    if (abortControllerRef.current) {
      abortControllerRef.current.abort();
      abortControllerRef.current = null;
    }
    dispatch({ type: "SET_IS_LOADING", payload: false });
    dispatch({
      type: "ADD_MESSAGE",
      payload: {
        id: `cancel-${Date.now()}`,
        sender: "assistant",
        text: "🛑 **Consulta cancelada por você.**",
        timestamp: new Date().toLocaleTimeString("pt-BR", {
          hour: "2-digit",
          minute: "2-digit",
        }),
      },
    });
  };

  const handleReset = () => {
    const welcomeMsg: ChatMessage = {
      id: "msg-welcome",
      sender: "assistant",
      text: `Olá! Sou o **Assistente Fiscal AI** do Portal da Transparência. Como posso ajudar nas suas consultas sobre o exercício de **${ano}**?`,
      timestamp: new Date().toLocaleTimeString("pt-BR", {
        hour: "2-digit",
        minute: "2-digit",
      }),
    };
    resetConversation(welcomeMsg);
  };

  const handleExportCsv = (msg: ChatMessage) => {
    if (!msg.responseObj?.chartData || msg.responseObj.chartData.length === 0)
      return;
    const header = "Categoria/Item,Valor\n";
    const rows = msg.responseObj.chartData
      .map((d) => `"${d.label.replace(/"/g, '""')}",${d.valor}`)
      .join("\n");
    const blob = new Blob([header + rows], { type: "text/csv;charset=utf-8;" });
    const url = URL.createObjectURL(blob);
    const link = document.createElement("a");
    link.setAttribute("href", url);
    link.setAttribute("download", `dados_assistente_${msg.id}.csv`);
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
  };

  const handleSendMessage = async (customMessage?: string) => {
    const textToSend = customMessage || state.inputMessage;
    if (!textToSend.trim() || state.isLoading) return;

    const userMsg: ChatMessage = {
      id: `user-${Date.now()}`,
      sender: "user",
      text: textToSend,
      timestamp: new Date().toLocaleTimeString("pt-BR", {
        hour: "2-digit",
        minute: "2-digit",
      }),
    };

    dispatch({ type: "ADD_MESSAGE", payload: userMsg });
    if (!customMessage) dispatch({ type: "SET_INPUT_MESSAGE", payload: "" });
    dispatch({ type: "SET_IS_LOADING", payload: true });

    const controller = new AbortController();
    abortControllerRef.current = controller;

    try {
      const res = await fetch("/api/assistant/chat", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        signal: controller.signal,
        body: JSON.stringify({
          message: textToSend,
          messagesHistory: state.messages.map((m) => ({
            sender: m.sender,
            text: m.text,
          })),
          portalSlug,
          ano,
          currentRoute: pathname || "/visao-geral",
        }),
      });

      if (!res.ok) throw new Error("Falha na consulta do assistente.");

      const data: AssistantResponse = await res.json();
      const assistantMsg: ChatMessage = {
        id: `assistant-${Date.now()}`,
        sender: "assistant",
        text: data.answer,
        responseObj: data,
        timestamp: new Date().toLocaleTimeString("pt-BR", {
          hour: "2-digit",
          minute: "2-digit",
        }),
      };

      dispatch({ type: "ADD_MESSAGE", payload: assistantMsg });
    } catch (error) {
      if (error instanceof Error && error.name === "AbortError") {
        return;
      }
      dispatch({
        type: "ADD_MESSAGE",
        payload: {
          id: `err-${Date.now()}`,
          sender: "assistant",
          text: "Desculpe, ocorreu um erro ao consultar os dados fiscais. Por favor, tente novamente em instantes.",
          timestamp: new Date().toLocaleTimeString("pt-BR", {
            hour: "2-digit",
            minute: "2-digit",
          }),
        },
      });
    } finally {
      dispatch({ type: "SET_IS_LOADING", payload: false });
      abortControllerRef.current = null;
    }
  };

  const drawerContent = state.isOpen ? (
    <div className="fixed inset-0 z-[9999] flex justify-end">
      <button
        type="button"
        aria-label="Fechar assistente"
        className="fixed inset-0 border-none bg-black/50 backdrop-blur-xs transition-opacity"
        onClick={() => dispatch({ type: "SET_IS_OPEN", payload: false })}
      />

      {/* Painel da Gaveta (Right Drawer) */}
      <div className="relative z-[10000] flex h-full w-full max-w-md flex-col border-borderLine border-l bg-white shadow-2xl transition-all">
        {/* Cabeçalho do Chat */}
        <div className="flex shrink-0 items-center justify-between border-borderLine border-b bg-slate-900 px-4 py-3.5 text-white">
          <div className="flex items-center gap-2.5">
            <div className="flex h-8 w-8 items-center justify-center rounded-lg bg-indigo-500/20 text-indigo-300">
              <Bot className="h-5 w-5" />
            </div>
            <div>
              <h2 className="font-bold text-sm leading-none">
                Assistente Fiscal AI
              </h2>
              <p className="mt-0.5 text-[11px] text-slate-300">
                Consulta inteligente de dados fiscais
              </p>
            </div>
          </div>
          <div className="flex items-center gap-1.5">
            <button
              type="button"
              onClick={handleReset}
              className="flex items-center gap-1 rounded-lg px-2 py-1 text-[11px] text-slate-300 transition-colors hover:bg-slate-800 hover:text-white"
              title="Nova Conversa / Limpar Histórico"
              aria-label="Nova Conversa"
            >
              <RotateCcw className="h-3.5 w-3.5" />
              <span>Nova Conversa</span>
            </button>
            <button
              type="button"
              onClick={() => dispatch({ type: "SET_IS_OPEN", payload: false })}
              className="rounded-lg p-1 text-slate-400 hover:bg-slate-800 hover:text-white"
              aria-label="Fechar"
            >
              <X className="h-5 w-5" />
            </button>
          </div>
        </div>

        {/* Mensagens do Chat */}
        <div className="flex-1 space-y-4 overflow-y-auto p-4">
          {state.messages.map((msg) => (
            <div
              key={msg.id}
              className={`flex flex-col ${
                msg.sender === "user" ? "items-end" : "items-start"
              }`}
            >
              <div
                className={`max-w-[85%] rounded-2xl px-4 py-3 text-xs leading-relaxed ${
                  msg.sender === "user"
                    ? "rounded-br-xs bg-indigo-600 text-white"
                    : "rounded-bl-xs border border-slate-200 bg-slate-100 text-slate-900"
                }`}
              >
                <div className="whitespace-pre-line font-normal">
                  <FormattedMarkdown text={msg.text} />
                </div>

                {/* Exibição de Mini-Cards de Métricas */}
                {Array.isArray(msg.responseObj?.metrics) &&
                  msg.responseObj.metrics.length > 0 && (
                    <div className="mt-3 grid grid-cols-1 gap-2 sm:grid-cols-2">
                      {msg.responseObj.metrics.map((card, idx) => (
                        <div
                          key={card.title || `card-${idx}`}
                          className="rounded-xl border border-slate-200 bg-white p-2.5 shadow-xs"
                        >
                          <p className="font-semibold text-[10px] text-slate-500 uppercase tracking-wider">
                            {card.title}
                          </p>
                          <p className="mt-1 font-bold text-slate-900 text-sm">
                            {card.value}
                          </p>
                        </div>
                      ))}
                    </div>
                  )}

                {/* Exibição de Gráfico Inline Simples & Botão Exportar CSV */}
                {Array.isArray(msg.responseObj?.chartData) &&
                  msg.responseObj.chartData.length > 0 && (
                    <div className="mt-3 space-y-2 rounded-xl border border-slate-200 bg-white p-3">
                      <div className="flex items-center justify-between">
                        <p className="font-semibold text-[10px] text-slate-500 uppercase tracking-wider">
                          Comparativo Visual
                        </p>
                        <button
                          type="button"
                          onClick={() => handleExportCsv(msg)}
                          className="flex items-center gap-1 font-medium text-[10px] text-indigo-600 hover:underline"
                          title="Exportar dados para CSV"
                        >
                          <Download className="h-3 w-3" />
                          <span>Exportar CSV</span>
                        </button>
                      </div>
                      {(() => {
                        const chartItems = msg.responseObj.chartData || [];
                        const values = chartItems.map((d) =>
                          typeof d?.valor === "number" && !Number.isNaN(d.valor)
                            ? d.valor
                            : 0,
                        );
                        const maxVal = Math.max(...values, 1);
                        return chartItems.map((pt, idx) => {
                          const val =
                            typeof pt?.valor === "number" &&
                            !Number.isNaN(pt.valor)
                              ? pt.valor
                              : 0;
                          const pct = maxVal > 0 ? (val / maxVal) * 100 : 0;
                          const label = pt?.label || `Item ${idx + 1}`;

                          return (
                            <div key={label} className="space-y-1">
                              <div className="flex justify-between font-medium text-[11px] text-slate-700">
                                <span>{label}</span>
                                <span>
                                  {pt.formattedValue ??
                                    (/servidor|pessoa|quantidade|qtd|unidade|porcentagem|pct|%|taxa|total|cargo|efetivo|contratado|outros/i.test(
                                      label,
                                    )
                                      ? val.toLocaleString("pt-BR")
                                      : new Intl.NumberFormat("pt-BR", {
                                          style: "currency",
                                          currency: "BRL",
                                        }).format(val))}
                                </span>
                              </div>
                              <div className="h-1.5 w-full overflow-hidden rounded-full bg-slate-100">
                                <div
                                  className="h-full rounded-full bg-indigo-600 transition-all"
                                  style={{
                                    width: `${Math.min(100, Math.max(5, pct))}%`,
                                  }}
                                />
                              </div>
                            </div>
                          );
                        });
                      })()}
                    </div>
                  )}

                {/* Exibição de Consulta SQL Apenas em Desenvolvimento (!isProduction) */}
                {!isProduction && msg.responseObj?.sqlQuery && (
                  <div className="mt-2.5 border-slate-200/60 border-t pt-2">
                    <button
                      type="button"
                      onClick={() =>
                        dispatch({ type: "TOGGLE_SQL_FOR", payload: msg.id })
                      }
                      className="flex items-center gap-1 font-medium text-[10px] text-indigo-600 hover:underline"
                    >
                      <Database className="h-3 w-3" />
                      <span>
                        {state.showSqlFor[msg.id]
                          ? "Ocultar SQL"
                          : "Ver consulta aos dados"}
                      </span>
                    </button>
                    {state.showSqlFor[msg.id] && (
                      <pre className="mt-1 max-w-full overflow-x-auto rounded-lg bg-slate-950 p-2 font-mono text-[10px] text-emerald-400 leading-tight">
                        {msg.responseObj.sqlQuery}
                      </pre>
                    )}
                  </div>
                )}

                {/* Barra de Feedback do Usuário (Thumbs up / Thumbs down) */}
                {msg.sender === "assistant" && msg.id !== "msg-welcome" && (
                  <div className="mt-2.5 flex items-center justify-between border-slate-200/60 border-t pt-1.5 text-[10px] text-slate-500">
                    <span className="text-[10px]">Essa resposta foi útil?</span>
                    <div className="flex items-center gap-1.5">
                      <button
                        type="button"
                        onClick={() => handleFeedback(msg.id, msg.text, 1)}
                        className={`flex items-center gap-1 rounded-md px-1.5 py-0.5 transition-colors ${
                          state.feedbackFor[msg.id] === 1
                            ? "bg-emerald-100 font-semibold text-emerald-700"
                            : "text-slate-600 hover:bg-slate-200"
                        }`}
                        title="Resposta útil"
                        aria-label="Resposta útil"
                      >
                        <ThumbsUp className="h-3 w-3" />
                      </button>
                      <button
                        type="button"
                        onClick={() => handleFeedback(msg.id, msg.text, -1)}
                        className={`flex items-center gap-1 rounded-md px-1.5 py-0.5 transition-colors ${
                          state.feedbackFor[msg.id] === -1
                            ? "bg-red-100 font-semibold text-red-700"
                            : "text-slate-600 hover:bg-slate-200"
                        }`}
                        title="Resposta imprecisa ou com erro"
                        aria-label="Resposta imprecisa ou com erro"
                      >
                        <ThumbsDown className="h-3 w-3" />
                      </button>
                      {state.feedbackFor[msg.id] !== undefined && (
                        <span className="font-medium text-[9px] text-emerald-600">
                          {state.feedbackFor[msg.id] === 1
                            ? "Obrigado!"
                            : "Agradecemos o aviso!"}
                        </span>
                      )}
                    </div>
                  </div>
                )}
              </div>
              <span className="mt-1 px-1 font-mono text-[9px] text-slate-400">
                {msg.timestamp}
              </span>
            </div>
          ))}

          {state.isLoading && (
            <div className="flex items-center justify-between rounded-xl border border-indigo-100 bg-indigo-50/60 p-2.5 font-medium text-indigo-900 text-xs">
              <div className="flex items-center gap-2">
                <Loader2 className="h-4 w-4 animate-spin text-indigo-600" />
                <span>Consultando dados fiscais...</span>
              </div>
              <button
                type="button"
                onClick={handleCancelRequest}
                className="flex items-center gap-1 rounded-lg border border-red-200 bg-red-50 px-2 py-1 font-semibold text-[10px] text-red-600 hover:bg-red-100"
              >
                <Square className="h-3 w-3 fill-red-600" />
                <span>Cancelar</span>
              </button>
            </div>
          )}
          <div ref={messagesEndRef} />
        </div>

        {/* Sugestões de Perguntas Rápidas com Colapso Automático e Toggle */}
        <div className="shrink-0 space-y-2 border-borderLine border-t bg-slate-50/50 p-3">
          <div className="flex items-center justify-between">
            <p className="flex items-center gap-1 font-semibold text-[10px] text-slate-500 uppercase tracking-wider">
              <Sparkles className="h-3 w-3 text-indigo-500" />
              Sugestões Rápidas
            </p>
            <button
              type="button"
              onClick={() =>
                dispatch({
                  type: "SET_SUGGESTIONS_EXPANDED",
                  payload: !state.suggestionsExpanded,
                })
              }
              className="flex items-center gap-0.5 text-[10px] text-indigo-600 hover:underline"
            >
              <span>{state.suggestionsExpanded ? "Recolher" : "Expandir"}</span>
              {state.suggestionsExpanded ? (
                <ChevronUp className="h-3 w-3" />
              ) : (
                <ChevronDown className="h-3 w-3" />
              )}
            </button>
          </div>

          {state.suggestionsExpanded && (
            <div className="flex flex-wrap gap-1.5">
              {activeSuggestedQuestions.map((q) => (
                <button
                  key={q}
                  type="button"
                  onClick={() => handleSendMessage(q)}
                  disabled={state.isLoading}
                  className="flex items-center gap-1 rounded-full border border-indigo-100 bg-white px-2.5 py-1 text-[11px] text-indigo-900 shadow-2xs transition-colors hover:border-indigo-300 hover:bg-indigo-50/50 disabled:opacity-50"
                >
                  <span>{q}</span>
                  <ChevronRight className="h-3 w-3 text-indigo-400" />
                </button>
              ))}
            </div>
          )}
        </div>

        {/* Disclaimer Legal Estático */}
        <div className="shrink-0 border-slate-100 border-t bg-slate-50/80 px-3 py-1.5 text-center text-[10px] text-slate-400">
          <p className="flex items-center justify-center gap-1">
            <Info className="h-3 w-3 shrink-0 text-slate-400" />
            <span>
              Dados informativos. Consulte os demonstrativos oficiais em Diário
              Oficial para fins jurídicos.
            </span>
          </p>
        </div>

        {/* Input de Envio de Mensagem */}
        <div className="shrink-0 border-borderLine border-t bg-white p-3">
          <form
            onSubmit={(e) => {
              e.preventDefault();
              handleSendMessage();
            }}
            className="flex items-center gap-2"
          >
            <input
              type="text"
              value={state.inputMessage}
              onChange={(e) =>
                dispatch({
                  type: "SET_INPUT_MESSAGE",
                  payload: e.target.value,
                })
              }
              placeholder="Pergunte sobre receitas, despesas, saúde..."
              disabled={state.isLoading}
              className="flex-1 rounded-xl border border-slate-200 bg-slate-50 px-3.5 py-2.5 text-slate-900 text-xs placeholder:text-slate-400 focus:border-indigo-500 focus:bg-white focus:outline-none"
            />
            {state.isLoading ? (
              <button
                type="button"
                onClick={handleCancelRequest}
                className="flex h-9 items-center gap-1 rounded-xl bg-red-600 px-3 font-semibold text-white text-xs shadow-xs hover:bg-red-700"
                aria-label="Cancelar consulta"
              >
                <Square className="h-3.5 w-3.5 fill-white" />
                <span>Parar</span>
              </button>
            ) : (
              <button
                type="submit"
                disabled={!state.inputMessage.trim()}
                className="flex h-9 w-9 items-center justify-center rounded-xl bg-indigo-600 text-white shadow-xs transition-colors hover:bg-indigo-700 disabled:opacity-50"
                aria-label="Enviar"
              >
                <Send className="h-4 w-4" />
              </button>
            )}
          </form>
        </div>
      </div>
    </div>
  ) : null;

  return (
    <>
      {/* Botão de Acionamento Flutuante / Header na Sidebar */}
      <button
        type="button"
        onClick={() => dispatch({ type: "SET_IS_OPEN", payload: true })}
        className="flex min-h-11 w-full cursor-pointer items-center justify-between rounded-lg border border-indigo-200 bg-gradient-to-r from-indigo-50 to-blue-50 px-3 py-2.5 font-semibold text-indigo-900 text-xs shadow-xs transition-all hover:border-indigo-300 hover:bg-indigo-100/50 active:scale-[0.99] sm:min-h-0"
      >
        <div className="flex items-center gap-2">
          <Sparkles className="h-4 w-4 shrink-0 text-indigo-600" />
          <span>Perguntar aos Dados</span>
        </div>
      </button>

      {/* Renderização da Gaveta com React Portal */}
      {mounted && drawerContent
        ? createPortal(drawerContent, document.body)
        : null}
    </>
  );
}

export function AssistantChatDrawer(props: AssistantChatDrawerProps) {
  return (
    <AssistantProvider portalSlug={props.portalSlug} ano={props.ano}>
      <AssistantChatDrawerContent {...props} />
    </AssistantProvider>
  );
}
