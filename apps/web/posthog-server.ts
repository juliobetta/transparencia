import { PostHog } from "posthog-node";

let posthogInstance: PostHog | null = null;

// Singleton do cliente server-side do PostHog, usado pelo hook `onRequestError`
// em `instrumentation.ts`. Sem isso, apenas exceções client-side eram
// capturadas e erros de render de Server Components chegavam mascarados
// (mensagem removida pelo Next.js), impossibilitando o diagnóstico.
export function getPostHogServer(): PostHog | null {
  const token = process.env.NEXT_PUBLIC_POSTHOG_PROJECT_TOKEN;
  if (!token) return null;

  if (!posthogInstance) {
    posthogInstance = new PostHog(token, {
      host: process.env.NEXT_PUBLIC_POSTHOG_HOST || "https://us.i.posthog.com",
      // Ambiente serverless: envia imediatamente em vez de acumular em buffer,
      // já que a instância pode ser congelada logo após a resposta.
      flushAt: 1,
      flushInterval: 0,
    });
  }

  return posthogInstance;
}
