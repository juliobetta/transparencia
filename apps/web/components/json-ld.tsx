export interface JsonLdProps {
  schema: Record<string, unknown>;
}

export function JsonLd({ schema }: JsonLdProps) {
  return (
    <script
      type="application/ld+json"
      // biome-ignore lint/security/noDangerouslySetInnerHtml: JSON-LD script tag insertion
      dangerouslySetInnerHTML={{ __html: JSON.stringify(schema) }}
    />
  );
}

export interface GovernmentOrganizationParams {
  displayName?: string;
  stateUF?: string;
  officialPortalUrl?: string;
}

export function generateGovernmentOrganizationSchema({
  displayName,
  stateUF,
  officialPortalUrl,
}: GovernmentOrganizationParams): Record<string, unknown> {
  const portalName = displayName || "Prefeitura Municipal";
  const portalUrl =
    officialPortalUrl || "https://transparencia.porciuncula.rj.gov.br";

  return {
    "@context": "https://schema.org",
    "@type": "GovernmentOrganization",
    name: portalName,
    url: portalUrl,
    address: {
      "@type": "PostalAddress",
      addressRegion: stateUF || "RJ",
      addressCountry: "BR",
    },
    knowsAbout: [
      "Transparência Pública",
      "Execução Orçamentária",
      "Contabilidade Pública STN/MCASP",
      "Lei de Responsabilidade Fiscal",
    ],
  };
}

export function generateDataCatalogSchema({
  displayName,
  officialPortalUrl,
}: GovernmentOrganizationParams): Record<string, unknown> {
  const portalName = displayName || "Prefeitura Municipal";
  const portalUrl =
    officialPortalUrl || "https://transparencia.porciuncula.rj.gov.br";

  return {
    "@context": "https://schema.org",
    "@type": "DataCatalog",
    name: `Portal de Dados da Transparência - ${portalName}`,
    description: `Catálogo público de conjuntos de dados orçamentários, fiscais, previdenciários e operacionais do município.`,
    url: portalUrl,
    publisher: {
      "@type": "GovernmentOrganization",
      name: portalName,
      url: portalUrl,
    },
    dataset: [
      {
        "@type": "Dataset",
        name: "Posição Fiscal e Restos a Pagar",
        description:
          "Balanço consolidado da arrecadação, despesas pagas e saldo de restos a pagar por gestão.",
        license: "https://creativecommons.org/licenses/by/4.0/",
        isAccessibleForFree: true,
      },
      {
        "@type": "Dataset",
        name: "Execução das Despesas Públicas",
        description:
          "Detalhamento de empenhos, liquidações e pagamentos por órgão, unidade e função contábil.",
        license: "https://creativecommons.org/licenses/by/4.0/",
        isAccessibleForFree: true,
      },
      {
        "@type": "Dataset",
        name: "Receitas Orçamentárias e Transferências Especiais (PIX)",
        description:
          "Arrecadação de receitas próprias, transferências constitucionais e repasses por emendas parlamentares.",
        license: "https://creativecommons.org/licenses/by/4.0/",
        isAccessibleForFree: true,
      },
      {
        "@type": "Dataset",
        name: "Licitações, Dispensas e Contratos Administrativos",
        description:
          "Catálogo de processos licitatórios, atos de adesão a atas de registro de preços e contratos ativos.",
        license: "https://creativecommons.org/licenses/by/4.0/",
        isAccessibleForFree: true,
      },
      {
        "@type": "Dataset",
        name: "Pessoal, Cargos e Folha de Pagamento",
        description:
          "Quadro de servidores públicos, despesa com pessoal para fins da LRF e distribuição de proventos.",
        license: "https://creativecommons.org/licenses/by/4.0/",
        isAccessibleForFree: true,
      },
      {
        "@type": "Dataset",
        name: "Situação Atuarial e RPPS (CAPREM)",
        description:
          "Indicadores de amortização de déficit atuarial e aportes previdenciários do instituto de previdência municipal.",
        license: "https://creativecommons.org/licenses/by/4.0/",
        isAccessibleForFree: true,
      },
      {
        "@type": "Dataset",
        name: "Aplicação na Saúde Pública",
        description:
          "Apuração do cumprimento do limite mínimo constitucional em saúde e fontes de recursos da área.",
        license: "https://creativecommons.org/licenses/by/4.0/",
        isAccessibleForFree: true,
      },
    ],
  };
}
