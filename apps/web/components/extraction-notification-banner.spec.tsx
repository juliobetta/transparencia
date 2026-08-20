import { fireEvent, render, screen } from "@testing-library/react";
import { beforeEach, describe, expect, it, vi } from "vitest";
import { ExtractionNotificationBanner } from "./extraction-notification-banner";

describe("ExtractionNotificationBanner Component", () => {
  beforeEach(() => {
    localStorage.clear();
    vi.restoreAllMocks();
  });

  it("does not render when lastExtractionDate is missing or matches localStorage", () => {
    const { container } = render(
      <ExtractionNotificationBanner portalName="Prefeitura de Porciúncula" />,
    );
    expect(container).toBeEmptyDOMElement();
  });

  it("renders notification banner when lastExtractionDate is newer than stored value", () => {
    localStorage.setItem("last_seen_extraction", "2026-08-01");

    render(
      <ExtractionNotificationBanner
        lastExtractionDate="2026-08-19"
        portalName="Prefeitura de Porciúncula"
      />,
    );

    expect(screen.getByText(/Novos dados disponíveis!/i)).toBeInTheDocument();
    expect(screen.getByText(/Prefeitura de Porciúncula/i)).toBeInTheDocument();
    expect(screen.getByText(/19\/08\/2026/)).toBeInTheDocument();
  });

  it("saves new extraction date to localStorage on dismiss", () => {
    localStorage.setItem("last_seen_extraction", "2026-08-01");

    render(
      <ExtractionNotificationBanner
        lastExtractionDate="2026-08-19"
        portalName="Prefeitura de Porciúncula"
      />,
    );

    const dismissButton = screen.getByRole("button", { name: "Entendido" });
    fireEvent.click(dismissButton);

    expect(localStorage.getItem("last_seen_extraction")).toBe("2026-08-19");
    expect(
      screen.queryByText(/Novos dados disponíveis!/i),
    ).not.toBeInTheDocument();
  });
});
