"use client";

import {
  Bot,
  ChevronRight,
  Database,
  Loader2,
  Send,
  Sparkles,
  Square,
  ThumbsDown,
  ThumbsUp,
  X,
} from "lucide-react";
import posthog from "posthog-js";
import { useEffect, useRef, useState } from "react";
import { createPortal } from "react-dom";
import type { AssistantResponse } from "../api/assistant/chat/route";

interface ChatMessage {
  id: string;
  sender: "user" | "assistant";
  text: string;
  responseObj?: AssistantResponse;
  timestamp: string;
}

const SUGGESTED_QUESTIONS = [
  "Qual a receita arrecadada este ano?",
  "Quanto foi gasto com a Saúde?",
  "Quais os aportes para o CAPREM?",
  "Qual o total em dispensas de licitação?",
];

interface AssistantChatDrawerProps {
  portalSlug?: string;
  ano?: string;
}

function FormattedMarkdown({ text }: { text: string }) {
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

export function AssistantChatDrawer({
  portalSlug = "porciuncula_prefeitura",
  ano = "2025",
}: AssistantChatDrawerProps) {
  const [isOpen, setIsOpen] = useState(false);
  const [mounted, setMounted] = useState(false);
  const [inputMessage, setInputMessage] = useState("");
  const [isLoading, setIsLoading] = useState(false);
  const [showSqlFor, setShowSqlFor] = useState<Record<string, boolean>>({});
  const [feedbackFor, setFeedbackFor] = useState<Record<string, 1 | -1>>({});
  const isProduction = process.env.NODE_ENV === "production";

  const handleFeedback = (msgId: string, text: string, score: 1 | -1) => {
    setFeedbackFor((prev) => ({ ...prev, [msgId]: score }));
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

  const [messages, setMessages] = useState<ChatMessage[]>([
    {
      id: "msg-welcome",
      sender: "assistant",
      text: `Olá! Sou o **Assistente Fiscal AI** do Portal da Transparência. Como posso ajudar nas suas consultas sobre o exercício de **${ano}**?`,
      timestamp: new Date().toLocaleTimeString("pt-BR", {
        hour: "2-digit",
        minute: "2-digit",
      }),
    },
  ]);

  const messagesEndRef = useRef<HTMLDivElement>(null);
  const abortControllerRef = useRef<AbortController | null>(null);

  useEffect(() => {
    setMounted(true);
  }, []);

  // biome-ignore lint/correctness/useExhaustiveDependencies: auto scroll on message update
  useEffect(() => {
    if (isOpen) {
      messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
    }
  }, [messages.length, isLoading, isOpen]);

  useEffect(() => {
    setMessages((prev) => {
      if (prev.length === 1 && prev[0].id === "msg-welcome") {
        return [
          {
            id: "msg-welcome",
            sender: "assistant",
            text: `Olá! Sou o **Assistente Fiscal AI** do Portal da Transparência. Como posso ajudar nas suas consultas sobre o exercício de **${ano}**?`,
            timestamp: new Date().toLocaleTimeString("pt-BR", {
              hour: "2-digit",
              minute: "2-digit",
            }),
          },
        ];
      }
      return prev;
    });
  }, [ano]);

  const handleCancelRequest = () => {
    if (abortControllerRef.current) {
      abortControllerRef.current.abort();
      abortControllerRef.current = null;
    }
    setIsLoading(false);
    setMessages((prev) => [
      ...prev,
      {
        id: `cancel-${Date.now()}`,
        sender: "assistant",
        text: "🛑 **Consulta cancelada por você.**",
        timestamp: new Date().toLocaleTimeString("pt-BR", {
          hour: "2-digit",
          minute: "2-digit",
        }),
      },
    ]);
  };

  const handleSendMessage = async (customMessage?: string) => {
    const textToSend = customMessage || inputMessage;
    if (!textToSend.trim() || isLoading) return;

    const userMsg: ChatMessage = {
      id: `user-${Date.now()}`,
      sender: "user",
      text: textToSend,
      timestamp: new Date().toLocaleTimeString("pt-BR", {
        hour: "2-digit",
        minute: "2-digit",
      }),
    };

    setMessages((prev) => [...prev, userMsg]);
    if (!customMessage) setInputMessage("");
    setIsLoading(true);

    const controller = new AbortController();
    abortControllerRef.current = controller;

    try {
      const res = await fetch("/api/assistant/chat", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        signal: controller.signal,
        body: JSON.stringify({
          message: textToSend,
          messagesHistory: messages.map((m) => ({
            sender: m.sender,
            text: m.text,
          })),
          portalSlug,
          ano,
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

      setMessages((prev) => [...prev, assistantMsg]);
    } catch (error) {
      if (error instanceof Error && error.name === "AbortError") {
        return;
      }
      setMessages((prev) => [
        ...prev,
        {
          id: `err-${Date.now()}`,
          sender: "assistant",
          text: "Desculpe, ocorreu um erro ao consultar os dados fiscais. Por favor, tente novamente em instantes.",
          timestamp: new Date().toLocaleTimeString("pt-BR", {
            hour: "2-digit",
            minute: "2-digit",
          }),
        },
      ]);
    } finally {
      setIsLoading(false);
      abortControllerRef.current = null;
    }
  };

  const toggleSqlDisplay = (msgId: string) => {
    setShowSqlFor((prev) => ({ ...prev, [msgId]: !prev[msgId] }));
  };

  const drawerContent = isOpen ? (
    <div className="fixed inset-0 z-[9999] flex justify-end">
      <button
        type="button"
        aria-label="Fechar assistente"
        className="fixed inset-0 border-none bg-black/50 backdrop-blur-xs transition-opacity"
        onClick={() => setIsOpen(false)}
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
          <button
            type="button"
            onClick={() => setIsOpen(false)}
            className="rounded-lg p-1 text-slate-400 hover:bg-slate-800 hover:text-white"
            aria-label="Fechar"
          >
            <X className="h-5 w-5" />
          </button>
        </div>

        {/* Mensagens do Chat */}
        <div className="flex-1 space-y-4 overflow-y-auto p-4">
          {messages.map((msg) => (
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
                {msg.responseObj?.metrics && (
                  <div className="mt-3 grid grid-cols-1 gap-2 sm:grid-cols-2">
                    {msg.responseObj.metrics.map((card) => (
                      <div
                        key={card.title}
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

                {/* Exibição de Gráfico Inline Simples */}
                {msg.responseObj?.chartData &&
                  msg.responseObj.chartData.length > 0 && (
                    <div className="mt-3 space-y-2 rounded-xl border border-slate-200 bg-white p-3">
                      <p className="font-semibold text-[10px] text-slate-500 uppercase tracking-wider">
                        Comparativo Visual
                      </p>
                      {(() => {
                        const chartItems = msg.responseObj.chartData;
                        const maxVal = Math.max(
                          ...chartItems.map((d) => d.valor),
                          1,
                        );
                        return chartItems.map((pt) => {
                          const pct =
                            maxVal > 0 ? (pt.valor / maxVal) * 100 : 0;
                          return (
                            <div key={pt.label} className="space-y-1">
                              <div className="flex justify-between font-medium text-[11px] text-slate-700">
                                <span>{pt.label}</span>
                                <span>
                                  {pt.formattedValue ??
                                    (/servidor|pessoa|quantidade|qtd|unidade|porcentagem|pct|%|taxa|total|cargo|efetivo|contratado|outros/i.test(
                                      pt.label,
                                    )
                                      ? pt.valor.toLocaleString("pt-BR")
                                      : new Intl.NumberFormat("pt-BR", {
                                          style: "currency",
                                          currency: "BRL",
                                        }).format(pt.valor))}
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
                      onClick={() => toggleSqlDisplay(msg.id)}
                      className="flex items-center gap-1 font-medium text-[10px] text-indigo-600 hover:underline"
                    >
                      <Database className="h-3 w-3" />
                      <span>
                        {showSqlFor[msg.id]
                          ? "Ocultar SQL"
                          : "Ver consulta aos dados"}
                      </span>
                    </button>
                    {showSqlFor[msg.id] && (
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
                          feedbackFor[msg.id] === 1
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
                          feedbackFor[msg.id] === -1
                            ? "bg-red-100 font-semibold text-red-700"
                            : "text-slate-600 hover:bg-slate-200"
                        }`}
                        title="Resposta imprecisa ou com erro"
                        aria-label="Resposta imprecisa ou com erro"
                      >
                        <ThumbsDown className="h-3 w-3" />
                      </button>
                      {feedbackFor[msg.id] !== undefined && (
                        <span className="font-medium text-[9px] text-emerald-600">
                          {feedbackFor[msg.id] === 1
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

          {isLoading && (
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

        {/* Sugestões de Perguntas Rápidas */}
        <div className="shrink-0 space-y-2 border-borderLine border-t bg-slate-50/50 p-3">
          <p className="flex items-center gap-1 font-semibold text-[10px] text-slate-500 uppercase tracking-wider">
            <Sparkles className="h-3 w-3 text-indigo-500" />
            Sugestões Rápidas
          </p>
          <div className="flex flex-wrap gap-1.5">
            {SUGGESTED_QUESTIONS.map((q) => (
              <button
                key={q}
                type="button"
                onClick={() => handleSendMessage(q)}
                disabled={isLoading}
                className="flex items-center gap-1 rounded-full border border-indigo-100 bg-white px-2.5 py-1 text-[11px] text-indigo-900 shadow-2xs transition-colors hover:border-indigo-300 hover:bg-indigo-50/50 disabled:opacity-50"
              >
                <span>{q}</span>
                <ChevronRight className="h-3 w-3 text-indigo-400" />
              </button>
            ))}
          </div>
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
              value={inputMessage}
              onChange={(e) => setInputMessage(e.target.value)}
              placeholder="Pergunte sobre receitas, despesas, saúde..."
              disabled={isLoading}
              className="flex-1 rounded-xl border border-slate-200 bg-slate-50 px-3.5 py-2.5 text-slate-900 text-xs placeholder:text-slate-400 focus:border-indigo-500 focus:bg-white focus:outline-none"
            />
            {isLoading ? (
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
                disabled={!inputMessage.trim()}
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
        onClick={() => setIsOpen(true)}
        className="flex min-h-[44px] w-full items-center justify-between rounded-lg border border-indigo-200 bg-gradient-to-r from-indigo-50 to-blue-50 px-3 py-2.5 font-semibold text-indigo-900 text-xs shadow-xs transition-all hover:border-indigo-300 hover:bg-indigo-100/50 active:scale-[0.99] sm:min-h-0"
      >
        <div className="flex items-center gap-2">
          <Sparkles className="h-4 w-4 shrink-0 text-indigo-600" />
          <span>Perguntar aos Dados</span>
        </div>
        <span className="rounded-full bg-indigo-600/10 px-2 py-0.5 font-bold text-[10px] text-indigo-700">
          AI MVP
        </span>
      </button>

      {/* Renderização da Gaveta com React Portal em document.body para garantir isolamento 100% de stacking context */}
      {mounted && drawerContent
        ? createPortal(drawerContent, document.body)
        : null}
    </>
  );
}
