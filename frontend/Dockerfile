# frontend/Dockerfile
FROM node:20-alpine AS deps
WORKDIR /app
COPY frontend/package.json frontend/package-lock.json* frontend/npm-shrinkwrap.json* ./ 
RUN npm ci

FROM node:20-alpine AS builder
WORKDIR /app
COPY --from=deps /app/node_modules ./node_modules
COPY frontend ./
# забираємо base URL API із ENV під час білду/рану
ARG NEXT_PUBLIC_API_BASE_URL
ENV NEXT_PUBLIC_API_BASE_URL=${NEXT_PUBLIC_API_BASE_URL}
RUN npm run build

FROM node:20-alpine AS runner
WORKDIR /app
ENV NODE_ENV=production PORT=3000
COPY --from=builder /app/.next ./.next
COPY --from=builder /app/public ./public
COPY --from=builder /app/package.json ./
COPY --from=builder /app/node_modules ./node_modules
EXPOSE 3000
CMD ["sh", "-lc", "node node_modules/next/dist/bin/next start -p $PORT"]
