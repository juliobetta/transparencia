"use client";

import { type MultiSelectOption, Sidebar } from "@transparencia/ui";
import { parseAsString, useQueryState } from "nuqs";
import posthog from "posthog-js";

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
    posthog.capture("year_filter_changed", {
      selected_year: val,
      previous_year: ano,
      portal_slug: portalSlug,
    });
    setAno(val);
  };

  const handleEntidadesChange = (ids: string[]) => {
    posthog.capture("entity_filter_changed", {
      selected_count: ids.length,
      portal_slug: portalSlug,
    });
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
