import { fireEvent, render, screen } from "@testing-library/react";
import posthog from "posthog-js";
import { beforeEach, describe, expect, it, vi } from "vitest";
import { ExtractionNotificationBanner } from "./extraction-notification-banner";

vi.mock("posthog-js", () => ({
  default: {
    capture: vi.fn(),
  },
}));

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

  it("renders notification banner and captures view event when lastExtractionDate is newer than stored value", () => {
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
    expect(posthog.capture).toHaveBeenCalledWith("extraction_banner_viewed", {
      last_extraction_date: "2026-08-19",
      portal_name: "Prefeitura de Porciúncula",
    });
  });

  it("saves new extraction date to localStorage and captures dismiss event on dismiss", () => {
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
    expect(posthog.capture).toHaveBeenCalledWith(
      "extraction_banner_dismissed",
      {
        last_extraction_date: "2026-08-19",
        portal_name: "Prefeitura de Porciúncula",
      },
    );
  });
});
