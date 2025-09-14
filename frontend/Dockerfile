FROM node:20-alpine AS builder
WORKDIR /app

# тільки файли залежностей
COPY package*.json ./
RUN npm ci

# код фронтенду (КОПІЮЄМО ПОТОЧНУ ПАПКУ, а не frontend/)
COPY . ./
RUN npm run build

# ---- продакшн ----
FROM node:20-alpine
WORKDIR /app

COPY --from=builder /app ./

ENV HOST=0.0.0.0 \
    PORT=3000

CMD ["npm", "start"]
