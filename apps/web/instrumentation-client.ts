import posthog from "posthog-js";

const token = process.env.NEXT_PUBLIC_POSTHOG_PROJECT_TOKEN;
const _host = process.env.NEXT_PUBLIC_POSTHOG_HOST;
const isProduction = process.env.NODE_ENV === "production";

if (token) {
  posthog.init(token, {
    api_host: "/ingest",
    ui_host: "https://us.posthog.com",
    // Include the defaults option as required by PostHog
    defaults: "2026-01-30",
    // Enable Error Tracking only in production, so dev-time compile
    // errors and hot-reload crashes don't pollute production issues.
    capture_exceptions: isProduction,
    // Turn on debug in development mode
    debug: process.env.NODE_ENV === "development",
  });
}

// IMPORTANT: Never combine this approach with other client-side PostHog initialization
// approaches, especially components like a PostHogProvider.
// instrumentation-client.ts is the correct solution for initializing client-side
// PostHog in Next.js 15.3+ apps.
