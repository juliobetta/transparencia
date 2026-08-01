"use client";

import { type MultiSelectOption, Sidebar } from "@transparencia/ui";
import { parseAsString, useQueryState } from "nuqs";
import posthog from "posthog-js";

const posthogConfigured = Boolean(
  process.env.NEXT_PUBLIC_POSTHOG_PROJECT_TOKEN &&
    process.env.NEXT_PUBLIC_POSTHOG_HOST,
);

interface SidebarWrapperProps {
  portalName?: string;
  stateUF?: string;
  portalTitle?: string;
  anoInicial?: number;
  lastExtractionDate?: string;
  officialPortalUrl?: string;
  brasaoAsset?: string;
  entidades?: MultiSelectOption[];
  portalSlug?: string;
}

export function SidebarWrapper({
  portalName,
  stateUF,
  portalTitle,
  anoInicial,
  lastExtractionDate,
  officialPortalUrl,
  brasaoAsset,
  entidades,
  portalSlug,
}: SidebarWrapperProps) {
  const currentYear = String(new Date().getFullYear());
  const [ano, setAno] = useQueryState(
    "ano",
    parseAsString.withDefault(currentYear).withOptions({ shallow: false }),
  );
  const [entidadesParam, setEntidadesParam] = useQueryState(
    "entidades",
    parseAsString.withOptions({ shallow: false }),
  );

  const selectedEntidades = entidadesParam
    ? entidadesParam.split(",").filter(Boolean)
    : [];

  const handleExerciceChange = (val: string) => {
    if (posthogConfigured && val !== ano) {
      posthog.capture("portal_year_filter_changed", {
        selected_year: val,
        portal_slug: portalSlug,
      });
    }
    setAno(val);
  };

  const handleEntidadesChange = (ids: string[]) => {
    if (posthogConfigured) {
      posthog.capture("portal_entities_filter_changed", {
        selected_entities_count: ids.length,
        portal_slug: portalSlug,
      });
    }

    if (ids.length === 0) {
      setEntidadesParam(null);
    } else {
      setEntidadesParam(ids.join(","));
    }
  };

  return (
    <Sidebar
      portalName={portalName}
      stateUF={stateUF}
      portalTitle={portalTitle}
      anoInicial={anoInicial}
      lastExtractionDate={lastExtractionDate}
      officialPortalUrl={officialPortalUrl}
      brasaoAsset={brasaoAsset}
      entidades={entidades}
      portalSlug={portalSlug}
      selectedExercice={ano}
      onExerciceChange={handleExerciceChange}
      selectedEntidades={selectedEntidades}
      onEntidadesChange={handleEntidadesChange}
    />
  );
}
