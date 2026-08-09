import { type NextRequest, NextResponse } from "next/server";

const RESERVED_STATIC_PATHS = new Set([
  "/favicon.ico",
  "/favicon.svg",
  "/favicon-32.png",
  "/favicon-180.png",
  "/robots.txt",
  "/sitemap.xml",
]);

export function proxy(request: NextRequest) {
  const { pathname } = request.nextUrl;

  // Proxy / intercept static assets so they never reach dynamic routes like [portalSlug]
  if (RESERVED_STATIC_PATHS.has(pathname) || pathname.startsWith("/ingest/")) {
    return NextResponse.next();
  }

  return NextResponse.next();
}

export const config = {
  matcher: [
    /*
     * Exclude static files, Next.js internal assets, and explicit favicons/robots/sitemap
     * from dynamic route resolution in [portalSlug].
     */
    "/((?!_next/static|_next/image|favicon\\.ico|favicon.*|robots\\.txt|sitemap\\.xml).*)",
  ],
};
