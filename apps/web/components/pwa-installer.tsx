"use client";

import posthog from "posthog-js";
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

function checkIsBannerDismissed(): boolean {
  return safeGetLocalStorage("pwa_dismissed") === "true";
}

export function PwaInstaller() {
  const [installPrompt, setInstallPrompt] =
    useState<BeforeInstallPromptEvent | null>(null);
  const [waitingWorker, setWaitingWorker] = useState<ServiceWorker | null>(
    null,
  );
  const [isStandalone, setIsStandalone] = useState(false);
  const [isDismissed, setIsDismissed] = useState(false);

  useEffect(() => {
    if (typeof window === "undefined") return;

    const standaloneOrInstalled = checkIsStandaloneOrInstalled();
    setIsStandalone(standaloneOrInstalled);
    setIsDismissed(checkIsBannerDismissed());

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

    let isMounted = true;
    let swRegistration: ServiceWorkerRegistration | null = null;
    let updateInterval: ReturnType<typeof setInterval> | null = null;
    let lastCheckedTime = 0;

    const checkForUpdates = (registration: ServiceWorkerRegistration) => {
      if (typeof navigator !== "undefined" && !navigator.onLine) return;
      const now = Date.now();
      if (now - lastCheckedTime < 60 * 1000) return; // Throttle checks to at most once per minute
      lastCheckedTime = now;
      registration.update().catch(() => {});
    };

    const handleFocus = () => {
      if (swRegistration) {
        checkForUpdates(swRegistration);
      }
    };

    navigator.serviceWorker
      .register("/sw.js")
      .then((registration) => {
        if (!isMounted) return;

        swRegistration = registration;
        if (registration.waiting && isMounted) {
          setWaitingWorker(registration.waiting);
        }

        registration.addEventListener("updatefound", () => {
          const newWorker = registration.installing;
          if (newWorker) {
            newWorker.addEventListener("statechange", () => {
              if (
                newWorker.state === "installed" &&
                navigator.serviceWorker.controller &&
                isMounted
              ) {
                setWaitingWorker(newWorker);
              }
            });
          }
        });

        // Check for updates on window focus and periodically every 15 minutes
        window.addEventListener("focus", handleFocus);
        updateInterval = setInterval(
          () => {
            if (isMounted && swRegistration) {
              checkForUpdates(swRegistration);
            }
          },
          15 * 60 * 1000,
        );
      })
      .catch((_error) => {});

    const handleBeforeInstallPrompt = (event: Event) => {
      if (checkIsStandaloneOrInstalled() || checkIsBannerDismissed()) return;

      event.preventDefault();
      setInstallPrompt(event as BeforeInstallPromptEvent);
      posthog.capture("pwa_install_banner_viewed");
    };

    const handleAppInstalled = () => {
      safeSetLocalStorage("pwa_installed", "true");
      setIsStandalone(true);
      setInstallPrompt(null);
    };

    window.addEventListener("beforeinstallprompt", handleBeforeInstallPrompt);
    window.addEventListener("appinstalled", handleAppInstalled);

    return () => {
      isMounted = false;
      if (updateInterval) clearInterval(updateInterval);
      window.removeEventListener("focus", handleFocus);
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

  useEffect(() => {
    if (waitingWorker) {
      posthog.capture("pwa_update_banner_viewed");
    }
  }, [waitingWorker]);

  const handleAppUpdate = () => {
    posthog.capture("pwa_update_clicked");
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

      {!isStandalone && !isDismissed && installPrompt && (
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
              posthog.capture("pwa_install_clicked");
              safeSetLocalStorage("pwa_dismissed", "true");
              setIsDismissed(true);
              installPrompt.prompt();
              installPrompt.userChoice
                .then((choiceResult: { outcome?: string }) => {
                  if (choiceResult?.outcome === "accepted") {
                    safeSetLocalStorage("pwa_installed", "true");
                    setIsStandalone(true);
                  }
                  setInstallPrompt(null);
                })
                .catch(() => {
                  setInstallPrompt(null);
                });
            }}
            className="shrink-0 cursor-pointer rounded-lg bg-blue-600 px-3.5 py-1.5 font-semibold text-white text-xs shadow-sm transition-colors hover:bg-blue-700"
          >
            Instalar
          </button>
          <button
            type="button"
            onClick={() => {
              posthog.capture("pwa_install_dismissed");
              safeSetLocalStorage("pwa_dismissed", "true");
              setIsDismissed(true);
              setInstallPrompt(null);
            }}
            className="px-1 font-bold text-slate-400 text-xs transition-colors hover:text-slate-600"
            title="Fechar"
            aria-label="Fechar"
          >
            ✕
          </button>
        </div>
      )}
    </>
  );
}
