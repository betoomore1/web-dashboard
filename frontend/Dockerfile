# frontend/Dockerfile
FROM node:20-alpine AS builder

WORKDIR /app

# копіюємо тільки package.json і lock-файли
COPY frontend/package*.json ./

# ставимо залежності
RUN npm ci

# копіюємо код фронтенду
COPY frontend/ ./

# білд
RUN npm run build

# ---- продакшн контейнер ----
FROM node:20-alpine

WORKDIR /app

# скопіюємо з builder
COPY --from=builder /app ./

ENV PORT=3000 \
    HOST=0.0.0.0

CMD ["npm", "start"]
