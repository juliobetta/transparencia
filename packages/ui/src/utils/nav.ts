export interface BuildNavUrlParams {
  path: string;
  slug?: string;
  exercice?: string;
  entidades?: string[];
}

export function buildNavUrl({
  path,
  slug,
  exercice,
  entidades,
}: BuildNavUrlParams): string {
  const slugPrefix = slug ? `/${slug}` : "";
  const basePath = path === "/" ? slugPrefix || "/" : `${slugPrefix}${path}`;

  const params = new URLSearchParams();
  if (exercice) {
    params.set("ano", exercice);
  }
  if (entidades && entidades.length > 0) {
    params.set("entidades", entidades.join(","));
  }
  const queryString = params.toString();
  return queryString ? `${basePath}?${queryString}` : basePath;
}
