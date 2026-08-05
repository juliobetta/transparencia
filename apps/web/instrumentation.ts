import type { Instrumentation } from "next";

// Captura erros que acontecem no servidor (render de Server Components, Route
// Handlers, etc.) e os envia ao PostHog. É o equivalente server-side do
// `instrumentation-client.ts`: sem este hook, o Next.js entrega ao cliente um
// erro genérico ("An error occurred in the Server Components render") com a
// mensagem e o stack removidos, e a causa real nunca chega ao Error Tracking.
export const onRequestError: Instrumentation.onRequestError = async (
  err,
  request,
  context,
) => {
  // O `onRequestError` também é chamado no runtime Edge, onde `posthog-node`
  // não roda. Só instrumentamos no runtime Node.js.
  if (process.env.NEXT_RUNTIME !== "nodejs") return;

  const { getPostHogServer } = await import("./posthog-server");
  const posthog = getPostHogServer();
  if (!posthog) return;

  // Recupera o distinct_id do cookie do PostHog quando disponível, para
  // correlacionar o erro de servidor com a sessão do visitante.
  let distinctId: string | undefined;
  const cookieHeader = request.headers.cookie;
  const cookie = Array.isArray(cookieHeader)
    ? cookieHeader.join("; ")
    : cookieHeader;
  if (cookie) {
    const match = cookie.match(/ph_phc_.*?_posthog=([^;]+)/);
    if (match) {
      try {
        const data = JSON.parse(decodeURIComponent(match[1]));
        distinctId = data.distinct_id;
      } catch {
        // Cookie malformado — segue sem distinct_id.
      }
    }
  }

  const error = err as Error & { digest?: string };

  posthog.captureException(error, distinctId, {
    // O `digest` é o identificador que o Next.js mostra ao usuário; guardá-lo
    // permite cruzar o erro exibido no cliente com o evento no PostHog.
    digest: error.digest,
    path: request.path,
    method: request.method,
    router_kind: context.routerKind,
    route_path: context.routePath,
    route_type: context.routeType,
    render_source: context.renderSource,
  });

  await posthog.flush();
};
