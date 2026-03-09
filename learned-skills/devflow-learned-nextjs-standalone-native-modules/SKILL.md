# Next.js Standalone + Native Node Modules (better-sqlite3, gamedig) in Docker

## Trigger

Use when:
- Docker build fails with `Error loading shared library ld-linux-x86-64.so.2` (Alpine + glibc binaries)
- `Failed to collect page data for /api/...` during `npm run build` on Alpine
- `gamedig`, `better-sqlite3`, or other modules with native binaries don't work in container
- Next.js standalone doesn't include modules with complex transitive dependencies (gamedig, got, etc.)

## Problem 1: Alpine vs glibc

`node:alpine` uses **musl libc**. Packages like `better-sqlite3` and `gamedig` distribute pre-compiled binaries for **glibc** (standard Linux). This causes runtime errors on Alpine.

**Fix: Switch the base image**

```dockerfile
# BEFORE (breaks with glibc binaries)
FROM node:22-alpine AS builder
FROM node:22-alpine AS runner

# AFTER (Debian slim = native glibc)
FROM node:22-slim AS builder
FROM node:22-slim AS runner
```

## Problem 2: Next.js build imports routes with native modules

Even POST-only routes are "inspected" by Next.js during build. If the route imports (transitively) `better-sqlite3` or any native `.node` module, the build fails.

**Fix: `force-dynamic` on ALL routes that import the DB (even indirectly)**

```typescript
// app/api/vip/webhook/route.ts — imports vip-service → db → better-sqlite3
export const dynamic = 'force-dynamic'

// app/api/vip/status/route.ts — imports db directly
export const dynamic = 'force-dynamic'
```

## Problem 3: Next.js standalone doesn't include transitive deps of complex packages

`gamedig` depends on `got`, `long`, `fast-xml-parser`, etc. Next.js file tracing doesn't track all these dependencies automatically.

**Fix: Copy full node_modules in the Dockerfile**

```dockerfile
FROM node:22-slim AS builder
WORKDIR /app
COPY package*.json ./
RUN npm ci
COPY . .
RUN npm run build

FROM node:22-slim AS runner
WORKDIR /app
ENV NODE_ENV=production
COPY --from=builder /app/.next/standalone ./
COPY --from=builder /app/.next/static ./.next/static
COPY --from=builder /app/public ./public
# gamedig and transitive deps are not auto-traced by standalone
COPY --from=builder /app/node_modules ./node_modules
EXPOSE 3000
CMD ["node", "server.js"]
```

**And in next.config.ts — mark as external to prevent bundling:**

```typescript
const nextConfig: NextConfig = {
  output: 'standalone',
  serverExternalPackages: ['better-sqlite3', 'gamedig'],
}
```

## Quick Diagnosis

```bash
# Check if module is in the container
docker exec <container> ls node_modules | grep gamedig

# Test module import
docker exec <container> node -e "require('gamedig'); console.log('ok')"

# See actual build error
docker compose build 2>&1 | grep -E 'Error|Failed|error' | grep -v node_modules
```
