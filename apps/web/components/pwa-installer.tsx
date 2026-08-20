"use client";

import { useEffect, useState } from "react";

interface BeforeInstallPromptEvent extends Event {
  prompt: () => void;
  userChoice: Promise<{ outcome: string }>;
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

function checkIsStandaloneOrInstalled(): boolean {
  if (typeof window === "undefined") return false;

  const isUrlStandalone = window.location.search.includes("mode=standalone");

  const isMatchMediaStandalone =
    typeof window.matchMedia === "function" &&
    (window.matchMedia("(display-mode: standalone)").matches ||
      window.matchMedia("(display-mode: window-controls-overlay)").matches ||
      window.matchMedia("(display-mode: minimal-ui)").matches ||
      window.matchMedia("(display-mode: fullscreen)").matches);

  const isNavigatorStandalone =
    (navigator as unknown as { standalone?: boolean }).standalone === true;

  const isReferrerApp =
    typeof document !== "undefined" &&
    document.referrer.includes("android-app://");

  const isLocalStorageInstalled =
    safeGetLocalStorage("pwa_installed") === "true";

  return (
    isUrlStandalone ||
    isMatchMediaStandalone ||
    isNavigatorStandalone ||
    isReferrerApp ||
    isLocalStorageInstalled
  );
}

export function PwaInstaller() {
  const [installPrompt, setInstallPrompt] =
    useState<BeforeInstallPromptEvent | null>(null);
  const [waitingWorker, setWaitingWorker] = useState<ServiceWorker | null>(
    null,
  );
  const [isStandalone, setIsStandalone] = useState(false);

  useEffect(() => {
    if (typeof window === "undefined") return;

    const standaloneOrInstalled = checkIsStandaloneOrInstalled();
    setIsStandalone(standaloneOrInstalled);

    if (!("serviceWorker" in navigator)) return;

    // Listen for controllerchange to reload page reliably after SKIP_WAITING
    let refreshing = false;
    const handleControllerChange = () => {
      if (!refreshing) {
        refreshing = true;
        window.location.reload();
      }
    };

    navigator.serviceWorker.addEventListener(
      "controllerchange",
      handleControllerChange,
    );

    navigator.serviceWorker
      .register("/sw.js")
      .then((registration) => {
        if (registration.waiting) {
          setWaitingWorker(registration.waiting);
        }

        registration.addEventListener("updatefound", () => {
          const newWorker = registration.installing;
          if (newWorker) {
            newWorker.addEventListener("statechange", () => {
              if (
                newWorker.state === "installed" &&
                navigator.serviceWorker.controller
              ) {
                setWaitingWorker(newWorker);
              }
            });
          }
        });
      })
      .catch((_error) => {});

    const handleBeforeInstallPrompt = (event: Event) => {
      if (checkIsStandaloneOrInstalled()) return;

      event.preventDefault();
      setInstallPrompt(event);
    };

    const handleAppInstalled = () => {
      safeSetLocalStorage("pwa_installed", "true");
      setIsStandalone(true);
      setInstallPrompt(null);
    };

    window.addEventListener("beforeinstallprompt", handleBeforeInstallPrompt);
    window.addEventListener("appinstalled", handleAppInstalled);

    return () => {
      if (typeof navigator.serviceWorker.removeEventListener === "function") {
        navigator.serviceWorker.removeEventListener(
          "controllerchange",
          handleControllerChange,
        );
      }
      window.removeEventListener(
        "beforeinstallprompt",
        handleBeforeInstallPrompt,
      );
      window.removeEventListener("appinstalled", handleAppInstalled);
    };
  }, []);

  const handleAppUpdate = () => {
    if (waitingWorker) {
      waitingWorker.postMessage({ type: "SKIP_WAITING" });
      setWaitingWorker(null);
    }
  };

  return (
    <>
      {waitingWorker && (
        <div className="fixed bottom-5 left-5 z-50 flex max-w-md items-center gap-3.5 rounded-xl border border-blue-200 bg-white p-4 text-slate-900 shadow-2xl ring-1 ring-slate-900/5">
          <div className="flex h-9 w-9 shrink-0 items-center justify-center rounded-lg bg-blue-100 font-bold text-base text-blue-600">
            🚀
          </div>
          <div className="flex-1 font-medium text-slate-900 text-sm">
            Nova versão da aplicação disponível!
          </div>
          <button
            type="button"
            onClick={handleAppUpdate}
            className="shrink-0 cursor-pointer rounded-lg bg-blue-600 px-3.5 py-1.5 font-semibold text-white text-xs shadow-sm transition-colors hover:bg-blue-700"
          >
            Atualizar Agora
          </button>
        </div>
      )}

      {!isStandalone && installPrompt && (
        <div className="fixed right-5 bottom-5 z-50 flex max-w-md items-center gap-3.5 rounded-xl border border-slate-200 bg-white p-4 text-slate-900 shadow-2xl ring-1 ring-slate-900/5">
          <div className="flex h-9 w-9 shrink-0 items-center justify-center rounded-lg bg-blue-50 font-bold text-base text-blue-600">
            📲
          </div>
          <div className="flex-1 font-medium text-slate-900 text-sm">
            Instale o App MaisTransparencia no seu dispositivo
          </div>
          <button
            type="button"
            onClick={() => {
              installPrompt.prompt();
              installPrompt.userChoice.then(
                (choiceResult: { outcome?: string }) => {
                  if (choiceResult?.outcome === "accepted") {
                    safeSetLocalStorage("pwa_installed", "true");
                    setIsStandalone(true);
                  }
                  setInstallPrompt(null);
                },
              );
            }}
            className="shrink-0 cursor-pointer rounded-lg bg-blue-600 px-3.5 py-1.5 font-semibold text-white text-xs shadow-sm transition-colors hover:bg-blue-700"
          >
            Instalar
          </button>
          <button
            type="button"
            onClick={() => setInstallPrompt(null)}
            className="px-1 font-bold text-slate-400 text-xs transition-colors hover:text-slate-600"
            title="Fechar"
          >
            ✕
          </button>
        </div>
      )}
    </>
  );
}
