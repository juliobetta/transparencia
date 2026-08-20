"use client";

import { useEffect, useState } from "react";

interface ExtractionNotificationBannerProps {
  lastExtractionDate?: string;
  portalName?: string;
}

function safeGetLocalStorage(key: string): string | null {
  try {
    return typeof window !== "undefined" ? localStorage.getItem(key) : null;
  } catch {
    return null;
  }
}

function safeSetLocalStorage(key: string, value: string): void {
  try {
    if (typeof window !== "undefined") {
      localStorage.setItem(key, value);
    }
  } catch {
    // Ignore storage quota or security errors
  }
}

function formatDateBR(dateStr?: string): string {
  if (!dateStr) return "";

  const cleanDate = dateStr.split("T")[0];
  const parts = cleanDate.split("-");

  if (parts.length === 3) {
    const [year, month, day] = parts;
    if (year.length === 4 && month.length === 2 && day.length === 2) {
      return `${day}/${month}/${year}`;
    }
  }

  try {
    const dateObj = new Date(dateStr);
    if (!Number.isNaN(dateObj.getTime())) {
      return new Intl.DateTimeFormat("pt-BR", { timeZone: "UTC" }).format(
        dateObj,
      );
    }
  } catch {
    // fallback to original string if parsing fails
  }

  return dateStr;
}

export function ExtractionNotificationBanner({
  lastExtractionDate,
  portalName = "Prefeitura de Porciúncula",
}: ExtractionNotificationBannerProps) {
  const [showNotificationBanner, setShowNotificationBanner] = useState(false);

  useEffect(() => {
    if (!lastExtractionDate || typeof window === "undefined") return;

    const storedExtractionDate = safeGetLocalStorage("last_seen_extraction");

    // Show banner if no date was previously saved or if a newer extraction is detected
    if (!storedExtractionDate || storedExtractionDate !== lastExtractionDate) {
      setShowNotificationBanner(true);

      const formattedDate = formatDateBR(lastExtractionDate);

      // Trigger OS/Browser native notification safely via Service Worker registration if granted
      if ("Notification" in window && Notification.permission === "granted") {
        if ("serviceWorker" in navigator) {
          navigator.serviceWorker.ready
            .then((registration) => {
              registration.showNotification("Novos Dados Fiscais Publicados", {
                body: `Novos dados de contas públicas foram carregados para ${portalName}. Data de extração: ${formattedDate}`,
                icon: "/favicon-192.png",
                badge: "/favicon-192.png",
                data: { url: "/" },
              });
            })
            .catch(() => {
              // Service worker ready fallback
            });
        }
      }
    }
  }, [lastExtractionDate, portalName]);

  const handleDismiss = () => {
    if (lastExtractionDate) {
      safeSetLocalStorage("last_seen_extraction", lastExtractionDate);
    }
    setShowNotificationBanner(false);
  };

  if (!showNotificationBanner) return null;

  const formattedDate = formatDateBR(lastExtractionDate);

  return (
    <div className="flex items-center justify-between border-blue-200 border-b bg-blue-50 px-4 py-2.5 text-blue-950 text-sm shadow-sm">
      <span className="flex items-center gap-2">
        <span>📢</span>
        <span>
          <strong>Novos dados disponíveis!</strong> A última extração de contas
          públicas de{" "}
          <span className="font-semibold text-blue-700">{portalName}</span> foi
          atualizada ({formattedDate}).
        </span>
      </span>
      <button
        type="button"
        onClick={handleDismiss}
        className="ml-4 rounded px-2.5 py-1 font-semibold text-blue-700 text-xs transition-colors hover:bg-blue-100"
      >
        Entendido
      </button>
    </div>
  );
}
