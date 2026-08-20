import { act, fireEvent, render, screen } from "@testing-library/react";
import posthog from "posthog-js";
import { beforeEach, describe, expect, it, vi } from "vitest";
import { PwaInstaller } from "./pwa-installer";

vi.mock("posthog-js", () => ({
  default: {
    capture: vi.fn(),
  },
}));

describe("PwaInstaller Component", () => {
  beforeEach(() => {
    vi.restoreAllMocks();
    localStorage.clear();

    window.matchMedia = vi.fn().mockImplementation((query) => ({
      matches: false,
      media: query,
      onchange: null,
      addListener: vi.fn(),
      removeListener: vi.fn(),
      addEventListener: vi.fn(),
      removeEventListener: vi.fn(),
      dispatchEvent: vi.fn(),
    }));

    const registerMock = vi.fn().mockResolvedValue({
      addEventListener: vi.fn(),
      waiting: null,
    });

    Object.defineProperty(navigator, "serviceWorker", {
      writable: true,
      value: {
        register: registerMock,
        addEventListener: vi.fn(),
        removeEventListener: vi.fn(),
      },
    });

    Object.defineProperty(window, "location", {
      writable: true,
      value: {
        ...window.location,
        reload: vi.fn(),
      },
    });
  });

  it("registers service worker on mount if supported", () => {
    render(<PwaInstaller />);
    expect(navigator.serviceWorker.register).toHaveBeenCalledWith("/sw.js");
  });

  it("renders install banner when beforeinstallprompt event fires", async () => {
    const promptMock = vi.fn();
    render(<PwaInstaller />);

    const beforeInstallEvent = new Event("beforeinstallprompt");
    Object.assign(beforeInstallEvent, {
      prompt: promptMock,
      userChoice: Promise.resolve({ outcome: "accepted" }),
    });

    act(() => {
      window.dispatchEvent(beforeInstallEvent);
    });

    expect(
      await screen.findByText(
        "Instale o App MaisTransparencia no seu dispositivo",
      ),
    ).toBeInTheDocument();
    expect(posthog.capture).toHaveBeenCalledWith("pwa_install_banner_viewed");

    const installButton = screen.getByRole("button", { name: "Instalar" });
    fireEvent.click(installButton);
    expect(promptMock).toHaveBeenCalled();
    expect(localStorage.getItem("pwa_dismissed")).toBe("true");
    expect(posthog.capture).toHaveBeenCalledWith("pwa_install_clicked");
  });

  it("renders update banner when a waiting service worker is detected", async () => {
    const postMessageMock = vi.fn();
    const waitingWorkerMock = {
      postMessage: postMessageMock,
    };

    const registerSpy = vi.spyOn(navigator.serviceWorker, "register");
    registerSpy.mockResolvedValueOnce({
      addEventListener: vi.fn(),
      waiting: waitingWorkerMock as unknown as ServiceWorker,
    } as unknown as ServiceWorkerRegistration);

    render(<PwaInstaller />);

    const updateBannerText = await screen.findByText(
      /Nova versão da aplicação disponível/i,
    );
    expect(updateBannerText).toBeInTheDocument();
    expect(posthog.capture).toHaveBeenCalledWith("pwa_update_banner_viewed");

    const updateButton = screen.getByRole("button", {
      name: "Atualizar Agora",
    });
    fireEvent.click(updateButton);
    expect(postMessageMock).toHaveBeenCalledWith({ type: "SKIP_WAITING" });
    expect(posthog.capture).toHaveBeenCalledWith("pwa_update_clicked");
  });

  it("suppresses install banner when running in standalone PWA mode", () => {
    window.matchMedia = vi.fn().mockImplementation((query) => ({
      matches: query === "(display-mode: standalone)",
      media: query,
      onchange: null,
      addListener: vi.fn(),
      removeListener: vi.fn(),
      addEventListener: vi.fn(),
      removeEventListener: vi.fn(),
      dispatchEvent: vi.fn(),
    }));

    render(<PwaInstaller />);

    const beforeInstallEvent = new Event("beforeinstallprompt");
    act(() => {
      window.dispatchEvent(beforeInstallEvent);
    });

    expect(
      screen.queryByText("Instale o App MaisTransparencia no seu dispositivo"),
    ).not.toBeInTheDocument();
  });

  it("persists dismissal when close button is clicked and suppresses banner on subsequent events", async () => {
    const promptMock = vi.fn();
    render(<PwaInstaller />);

    const beforeInstallEvent = new Event("beforeinstallprompt");
    Object.assign(beforeInstallEvent, {
      prompt: promptMock,
      userChoice: Promise.resolve({ outcome: "dismissed" }),
    });

    act(() => {
      window.dispatchEvent(beforeInstallEvent);
    });

    expect(
      await screen.findByText(
        "Instale o App MaisTransparencia no seu dispositivo",
      ),
    ).toBeInTheDocument();

    const closeButton = screen.getByRole("button", { name: "Fechar" });
    fireEvent.click(closeButton);

    expect(
      screen.queryByText("Instale o App MaisTransparencia no seu dispositivo"),
    ).not.toBeInTheDocument();

    expect(localStorage.getItem("pwa_dismissed")).toBe("true");
    expect(posthog.capture).toHaveBeenCalledWith("pwa_install_dismissed");
  });

  it("suppresses install banner when pwa_dismissed is set in localStorage", () => {
    localStorage.setItem("pwa_dismissed", "true");

    render(<PwaInstaller />);

    const beforeInstallEvent = new Event("beforeinstallprompt");
    act(() => {
      window.dispatchEvent(beforeInstallEvent);
    });

    expect(
      screen.queryByText("Instale o App MaisTransparencia no seu dispositivo"),
    ).not.toBeInTheDocument();
  });
});
