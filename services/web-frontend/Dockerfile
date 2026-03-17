# Stage 1: Install dependencies
FROM node:20-alpine AS dependencies

WORKDIR /app

# Copy package files relative to the project root context (as defined in docker-compose)
COPY services/web-frontend/package*.json ./

RUN npm ci && npm cache clean --force

# Stage 2: Copy source code, dependencies and build
FROM node:20-alpine AS builder

WORKDIR /app

COPY --from=dependencies /app/node_modules ./node_modules

# Copy source code relative to the project root context
COPY services/web-frontend/ ./

ENV NEXT_TELEMETRY_DISABLED=1

RUN npm run build

# Stage 3: Production image
FROM node:20-alpine AS runner

WORKDIR /app

ENV NODE_ENV=production
ENV NEXT_TELEMETRY_DISABLED=1

RUN addgroup --system --gid 1001 nodejs
RUN adduser --system --uid 1001 nextjs

# Copy standalone output and static files
COPY --from=builder /app/public ./public
COPY --from=builder --chown=nextjs:nodejs /app/.next/standalone ./
COPY --from=builder --chown=nextjs:nodejs /app/.next/static ./.next/static

USER nextjs

EXPOSE 3000

ENV PORT 3000
ENV HOSTNAME "0.0.0.0"

CMD ["node", "server.js"]