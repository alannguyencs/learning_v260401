const { createProxyMiddleware } = require("http-proxy-middleware");
const fs = require("fs");
const path = require("path");

// Read BACKEND_PORT from root .env
let backendPort = 8999;
const envPath = path.resolve(__dirname, "../../.env");
if (fs.existsSync(envPath)) {
  const envContent = fs.readFileSync(envPath, "utf-8");
  const match = envContent.match(/^BACKEND_PORT=(\d+)/m);
  if (match) {
    backendPort = match[1];
  }
}

module.exports = function (app) {
  const target = `http://localhost:${backendPort}`;

  // Single proxy for both HTTP and WebSocket traffic. The path filter is passed
  // as http-proxy-middleware's `context` (NOT an Express mount path) because the
  // WS `upgrade` handler is gated by `context`, not by Express routing. A
  // mount-path-only proxy would default `context` to "/" and forward EVERY
  // upgrade — including the dev-server's own `/ws` HMR socket — to the backend
  // (403 spam). This function context is evaluated for HTTP requests and WS
  // upgrades alike, so `/ws` is left with webpack-dev-server while
  // `/api/voice/v2v-over` reaches the backend.
  const forwardToBackend = (pathname) =>
    pathname.startsWith("/api") ||
    pathname.startsWith("/auth") ||
    pathname.startsWith("/health");

  app.use(
    createProxyMiddleware(forwardToBackend, {
      target,
      changeOrigin: true,
      ws: true,
    }),
  );
};
