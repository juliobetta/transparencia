const CACHE_VERSION = "v1";
const CACHE_NAME = `transparenciaweb-cache-${CACHE_VERSION}`;

const PRECACHE_ASSETS = [
  "/",
  "/manifest.webmanifest",
  "/favicon.svg",
  "/favicon-192.png",
  "/favicon-512.png",
];

self.addEventListener("install", (event) => {
  event.waitUntil(
    caches.open(CACHE_NAME).then((cache) => {
      return Promise.allSettled(
        PRECACHE_ASSETS.map((asset) =>
          cache.add(asset).catch(() => {
            // Log individual asset caching failure without aborting installation
          })
        )
      );
    })
  );
  self.skipWaiting();
});

self.addEventListener("activate", (event) => {
  event.waitUntil(
    caches.keys().then((cacheNames) => {
      return Promise.all(
        cacheNames
          .filter((name) => name.startsWith("transparenciaweb-cache-") && name !== CACHE_NAME)
          .map((name) => caches.delete(name))
      );
    })
  );
  self.clients.claim();
});

self.addEventListener("message", (event) => {
  if (event.data && event.data.type === "SKIP_WAITING") {
    self.skipWaiting();
  }
});

self.addEventListener("fetch", (event) => {
  if (event.request.method !== "GET") return;

  const url = new URL(event.request.url);

  // Ignore non-http(s) requests (e.g. chrome-extension://, moz-extension://)
  if (!url.protocol.startsWith("http")) return;

  // Ignore Next.js Dev Server HMR & WebSockets
  if (
    url.pathname.includes("webpack-hmr") ||
    url.pathname.includes("turbopack-hmr") ||
    event.request.headers.get("upgrade") === "websocket"
  ) {
    return;
  }

  // Cache-first for static assets (Next.js static files, images, icons, fonts)
  if (
    url.pathname.startsWith("/_next/static/") ||
    url.pathname.match(/\.(png|jpg|jpeg|svg|css|js|ico|woff2?)$/)
  ) {
    event.respondWith(
      caches.match(event.request).then((cachedResponse) => {
        if (cachedResponse) return cachedResponse;
        return fetch(event.request)
          .then((networkResponse) => {
            if (networkResponse.status === 200) {
              const responseClone = networkResponse.clone();
              caches.open(CACHE_NAME).then((cache) => {
                cache.put(event.request, responseClone).catch(() => {
                  // Ignore caching errors
                });
              });
            }
            return networkResponse;
          })
          .catch(() => {
            // Return empty 404 response for missing uncached static assets when offline
            return new Response(null, { status: 404 });
          });
      })
    );
    return;
  }

  // Network-first for dynamic routes and API calls
  event.respondWith(
    fetch(event.request).catch(() => {
      return caches.match(event.request).then((cachedResponse) => {
        if (cachedResponse) return cachedResponse;
        // Only return app shell HTML for page navigation requests when offline
        if (event.request.mode === "navigate") {
          return caches.match("/");
        }
        // For API/RSC requests, return 503 offline JSON response instead of HTML
        return new Response(JSON.stringify({ error: "Offline - No cached data available" }), {
          status: 503,
          headers: { "Content-Type": "application/json" },
        });
      });
    })
  );
});

self.addEventListener("push", (event) => {
  let data = {};
  try {
    data = event.data ? event.data.json() : {};
  } catch {
    data = { body: event.data ? event.data.text() : "" };
  }

  const title = data.title || "MaisTransparencia - Atualização Fiscal";
  const options = {
    body: data.body || "Novos dados fiscais foram disponibilizados no portal.",
    icon: "/favicon-192.png",
    badge: "/favicon-192.png",
    data: {
      url: data.url || "/",
    },
  };

  event.waitUntil(self.registration.showNotification(title, options));
});

self.addEventListener("notificationclick", (event) => {
  event.notification.close();
  const rawUrl = event.notification.data?.url || "/";

  // Sanitize targetUrl to ensure same-origin navigation (prevent open-redirect vulnerabilities)
  let resolvedUrl;
  try {
    resolvedUrl = new URL(rawUrl, self.location.origin);
    if (resolvedUrl.origin !== self.location.origin) {
      resolvedUrl = new URL("/", self.location.origin);
    }
  } catch {
    resolvedUrl = new URL("/", self.location.origin);
  }

  const absoluteTargetUrl = resolvedUrl.href;

  event.waitUntil(
    clients.matchAll({ type: "window", includeUncontrolled: true }).then((clientList) => {
      for (const client of clientList) {
        if (
          (client.url === absoluteTargetUrl ||
            new URL(client.url).pathname === resolvedUrl.pathname) &&
          "focus" in client
        ) {
          return client.focus();
        }
      }
      if (clients.openWindow) {
        return clients.openWindow(absoluteTargetUrl);
      }
    })
  );
});
