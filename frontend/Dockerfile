# Frontend Dockerfile
FROM node:24-alpine AS deps
# Check https://github.com/nodejs/docker-node/tree/b4117f9333da4138b03a546ec926ef50a31506c3#nodealpine to understand why libc6-compat might be needed.
RUN apk add --no-cache libc6-compat
WORKDIR /app

# Create non-root user for build stages
RUN addgroup -g 1001 -S nodejs && adduser -S nextjs -u 1001

# Install dependencies based on the preferred package manager
COPY --chown=nextjs:nodejs package.json package-lock.json* ./

# Create directories with proper permissions before switching user
RUN mkdir -p /app/.npm /app/node_modules && \
    chown -R nextjs:nodejs /app/.npm /app/node_modules /app

# Switch to non-root user
USER nextjs

# Set npm cache directory
ENV NPM_CONFIG_CACHE=/app/.npm

# Install dependencies
RUN npm ci --ignore-scripts

# Rebuild the source code only when needed
FROM node:24-alpine AS builder
WORKDIR /app

# Create non-root user for build stage
RUN addgroup -g 1001 -S nodejs && adduser -S nextjs -u 1001

COPY --from=deps --chown=nextjs:nodejs /app/node_modules ./node_modules
COPY --chown=nextjs:nodejs . .

USER nextjs

# Build the application
ENV NEXT_TELEMETRY_DISABLED=1
RUN npm run build

# Production image, copy all the files and run next
FROM node:24-alpine AS runner
WORKDIR /app

ENV NODE_ENV=production
ENV NEXT_TELEMETRY_DISABLED=1

# Create non-root user
RUN addgroup --system --gid 1001 nodejs
RUN adduser --system --uid 1001 nextjs

# Copy necessary files
COPY --from=builder /app/public ./public
COPY --from=builder --chown=nextjs:nodejs /app/.next/standalone ./
COPY --from=builder --chown=nextjs:nodejs /app/.next/static ./.next/static

# Copy health check script
COPY --chown=nextjs:nodejs healthcheck.js ./

USER nextjs

EXPOSE 3000

ENV PORT=3000

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD ["node", "healthcheck.js"]

CMD ["node", "server.js"]
