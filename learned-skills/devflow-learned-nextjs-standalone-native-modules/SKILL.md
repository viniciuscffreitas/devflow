# Next.js Standalone + Native Node Modules (better-sqlite3, gamedig) no Docker

## Trigger

Use quando:
- Build Docker falha com `Error loading shared library ld-linux-x86-64.so.2` (Alpine + glibc binaries)
- `Failed to collect page data for /api/...` durante `npm run build` no Alpine
- `gamedig`, `better-sqlite3`, ou outros módulos com binários nativos não funcionam em container
- Next.js standalone não inclui módulos com dependências transitivas complexas (gamedig, got, etc.)

## Problema 1: Alpine vs glibc

`node:alpine` usa **musl libc**. Pacotes como `better-sqlite3` e `gamedig` distribuem binários pré-compilados para **glibc** (Linux padrão). Isso causa erro em runtime no Alpine.

**Fix: Trocar a imagem base**

```dockerfile
# ANTES (quebra com glibc binaries)
FROM node:22-alpine AS builder
FROM node:22-alpine AS runner

# DEPOIS (Debian slim = glibc nativo)
FROM node:22-slim AS builder
FROM node:22-slim AS runner
```

## Problema 2: Next.js build faz import de rotas com native modules

Mesmo rotas POST-only são "inspecionadas" pelo Next.js durante o build. Se a rota importa (transitivamente) `better-sqlite3` ou qualquer `.node` nativo, o build falha.

**Fix: `force-dynamic` em TODAS as rotas que importam o DB (mesmo indiretamente)**

```typescript
// app/api/vip/webhook/route.ts — importa vip-service → db → better-sqlite3
export const dynamic = 'force-dynamic'

// app/api/vip/status/route.ts — importa db diretamente
export const dynamic = 'force-dynamic'
```

## Problema 3: Next.js standalone não inclui deps transitivas de pacotes complexos

`gamedig` depende de `got`, `long`, `fast-xml-parser`, etc. O file tracing do Next.js não rastreia todas essas dependências automaticamente.

**Fix: Copiar node_modules completo no Dockerfile**

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
# gamedig e deps transitivas não são auto-rastreadas pelo standalone
COPY --from=builder /app/node_modules ./node_modules
EXPOSE 3000
CMD ["node", "server.js"]
```

**E no next.config.ts — marcar como external para não tentar bundlar:**

```typescript
const nextConfig: NextConfig = {
  output: 'standalone',
  serverExternalPackages: ['better-sqlite3', 'gamedig'],
}
```

## Diagnóstico Rápido

```bash
# Verificar se módulo está no container
docker exec <container> ls node_modules | grep gamedig

# Testar import do módulo
docker exec <container> node -e "require('gamedig'); console.log('ok')"

# Ver erro real de build
docker compose build 2>&1 | grep -E 'Error|Failed|error' | grep -v node_modules
```
