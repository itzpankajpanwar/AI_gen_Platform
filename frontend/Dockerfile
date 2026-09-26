FROM node:22-alpine AS builder
WORKDIR /app

ARG NEXT_PUBLIC_API_BASE=http://localhost:8200
ENV NEXT_PUBLIC_API_BASE=$NEXT_PUBLIC_API_BASE

COPY frontend/package.json frontend/package-lock.json* ./
RUN npm install --no-audit --no-fund

COPY frontend/ ./
RUN npm run build

FROM node:22-alpine AS runner
WORKDIR /app
ENV NODE_ENV=production PORT=3200

COPY --from=builder /app/.next/standalone ./
COPY --from=builder /app/.next/static ./.next/static
COPY --from=builder /app/public ./public

EXPOSE 3200
CMD ["node", "server.js"]
