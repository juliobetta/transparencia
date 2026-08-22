"use client";

import type React from "react";
import { createContext, useContext, useEffect, useReducer } from "react";
import type { AssistantResponse } from "../api/assistant/chat/route";

export interface ChatMessage {
  id: string;
  sender: "user" | "assistant";
  text: string;
  responseObj?: AssistantResponse;
  timestamp: string;
}

export interface AssistantState {
  isOpen: boolean;
  inputMessage: string;
  isLoading: boolean;
  messages: ChatMessage[];
  showSqlFor: Record<string, boolean>;
  feedbackFor: Record<string, 1 | -1>;
  hasInteracted: boolean;
  suggestionsExpanded: boolean;
}

export type AssistantAction =
  | { type: "SET_IS_OPEN"; payload: boolean }
  | { type: "SET_INPUT_MESSAGE"; payload: string }
  | { type: "SET_IS_LOADING"; payload: boolean }
  | { type: "ADD_MESSAGE"; payload: ChatMessage }
  | { type: "SET_MESSAGES"; payload: ChatMessage[] }
  | { type: "TOGGLE_SQL_FOR"; payload: string }
  | { type: "SET_FEEDBACK_FOR"; payload: { messageId: string; score: 1 | -1 } }
  | { type: "SET_SUGGESTIONS_EXPANDED"; payload: boolean }
  | { type: "RESET_CONVERSATION"; payload: { welcomeMessage: ChatMessage } };

function getStorageKey(portalSlug?: string, ano?: string): string {
  const slug = portalSlug || "porciuncula_prefeitura";
  const year = ano || "2025";
  return `transparenciaweb_assistant_chat_${slug}_${year}`;
}

function createInitialState(welcomeMessage?: ChatMessage): AssistantState {
  const initialWelcome: ChatMessage = welcomeMessage ?? {
    id: "msg-welcome",
    sender: "assistant",
    text: "Olá! Sou o **Assistente Fiscal AI** do Portal da Transparência. Como posso ajudar nas suas consultas?",
    timestamp: "agora",
  };

  return {
    isOpen: false,
    inputMessage: "",
    isLoading: false,
    messages: [initialWelcome],
    showSqlFor: {},
    feedbackFor: {},
    hasInteracted: false,
    suggestionsExpanded: true,
  };
}

function assistantReducer(
  state: AssistantState,
  action: AssistantAction,
): AssistantState {
  switch (action.type) {
    case "SET_IS_OPEN":
      return { ...state, isOpen: action.payload };

    case "SET_INPUT_MESSAGE":
      return { ...state, inputMessage: action.payload };

    case "SET_IS_LOADING":
      return { ...state, isLoading: action.payload };

    case "ADD_MESSAGE": {
      const nextMessages = [...state.messages, action.payload];
      const isFirstUserMessage =
        action.payload.sender === "user" && !state.hasInteracted;
      return {
        ...state,
        messages: nextMessages,
        hasInteracted: state.hasInteracted || action.payload.sender === "user",
        suggestionsExpanded: isFirstUserMessage
          ? false
          : state.suggestionsExpanded,
      };
    }

    case "SET_MESSAGES":
      return {
        ...state,
        messages: action.payload,
        hasInteracted: action.payload.some((m) => m.sender === "user"),
        suggestionsExpanded: action.payload.some((m) => m.sender === "user")
          ? false
          : state.suggestionsExpanded,
      };

    case "TOGGLE_SQL_FOR": {
      const msgId = action.payload;
      return {
        ...state,
        showSqlFor: {
          ...state.showSqlFor,
          [msgId]: !state.showSqlFor[msgId],
        },
      };
    }

    case "SET_FEEDBACK_FOR":
      return {
        ...state,
        feedbackFor: {
          ...state.feedbackFor,
          [action.payload.messageId]: action.payload.score,
        },
      };

    case "SET_SUGGESTIONS_EXPANDED":
      return { ...state, suggestionsExpanded: action.payload };

    case "RESET_CONVERSATION":
      return {
        ...createInitialState(action.payload.welcomeMessage),
        isOpen: state.isOpen,
      };

    default:
      return state;
  }
}

interface AssistantContextType {
  state: AssistantState;
  dispatch: React.Dispatch<AssistantAction>;
  resetConversation: (welcomeMessage: ChatMessage) => void;
}

const AssistantContext = createContext<AssistantContextType | null>(null);

export interface AssistantProviderProps {
  children: React.ReactNode;
  portalSlug?: string;
  ano?: string;
}

export function AssistantProvider({
  children,
  portalSlug,
  ano,
}: AssistantProviderProps) {
  const [state, dispatch] = useReducer(assistantReducer, undefined, () =>
    createInitialState(),
  );
  const storageKey = getStorageKey(portalSlug, ano);

  // Restaurar do localStorage ao montar no cliente de forma segura e estritamente validada
  useEffect(() => {
    if (typeof window === "undefined") return;
    try {
      const saved = localStorage.getItem(storageKey);
      if (saved) {
        const parsed = JSON.parse(saved) as ChatMessage[];
        if (Array.isArray(parsed) && parsed.length > 0) {
          const validMessages: ChatMessage[] = [];
          for (const m of parsed) {
            if (
              m &&
              typeof m.id === "string" &&
              (m.sender === "user" || m.sender === "assistant") &&
              typeof m.text === "string"
            ) {
              validMessages.push({
                id: m.id,
                sender: m.sender,
                text: m.text,
                timestamp:
                  typeof m.timestamp === "string" ? m.timestamp : "agora",
                responseObj:
                  m.responseObj && typeof m.responseObj === "object"
                    ? {
                        answer:
                          typeof m.responseObj.answer === "string"
                            ? m.responseObj.answer
                            : m.text,
                        metrics: Array.isArray(m.responseObj.metrics)
                          ? m.responseObj.metrics
                          : undefined,
                        chartData: Array.isArray(m.responseObj.chartData)
                          ? m.responseObj.chartData
                          : undefined,
                        chartType: m.responseObj.chartType,
                        sqlQuery:
                          typeof m.responseObj.sqlQuery === "string"
                            ? m.responseObj.sqlQuery
                            : undefined,
                      }
                    : undefined,
              });
            }
          }
          if (validMessages.length > 0) {
            dispatch({ type: "SET_MESSAGES", payload: validMessages });
          }
        }
      }
    } catch (_e) {}
  }, [storageKey]);

  // Salvar no localStorage com limpeza de payload
  useEffect(() => {
    if (typeof window === "undefined") return;
    if (state.messages.length === 0) return;
    try {
      const cleanMessages = state.messages.map((m) => ({
        id: m.id,
        sender: m.sender,
        text: m.text,
        timestamp: m.timestamp,
        responseObj: m.responseObj
          ? {
              answer: m.responseObj.answer,
              metrics: Array.isArray(m.responseObj.metrics)
                ? m.responseObj.metrics
                : undefined,
              chartData: Array.isArray(m.responseObj.chartData)
                ? m.responseObj.chartData
                : undefined,
              chartType: m.responseObj.chartType,
              sqlQuery:
                typeof m.responseObj.sqlQuery === "string"
                  ? m.responseObj.sqlQuery
                  : undefined,
            }
          : undefined,
      }));
      localStorage.setItem(storageKey, JSON.stringify(cleanMessages));
    } catch (_e) {}
  }, [state.messages, storageKey]);

  const resetConversation = (welcomeMessage: ChatMessage) => {
    try {
      if (typeof window !== "undefined") {
        localStorage.removeItem(storageKey);
      }
    } catch (_e) {}
    dispatch({ type: "RESET_CONVERSATION", payload: { welcomeMessage } });
  };

  return (
    <AssistantContext.Provider value={{ state, dispatch, resetConversation }}>
      {children}
    </AssistantContext.Provider>
  );
}

export function useAssistantContext(): AssistantContextType {
  const context = useContext(AssistantContext);
  if (!context) {
    throw new Error(
      "useAssistantContext must be used within an AssistantProvider",
    );
  }
  return context;
}
