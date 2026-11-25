FROM node:22-alpine AS builder

WORKDIR /app

# Кеширование зависимостей
COPY package*.json tsconfig*.json vite.config.ts index.html ./
RUN npm ci --ignore-scripts

# Исходники и сборка
COPY . .
RUN npm run build

# Минимальный образ только с dist
FROM alpine:3.19
RUN apk add --no-cache rsync
COPY --from=builder /app/dist /app/dist
CMD ["rsync", "-a", "--delete", "/app/dist/", "/dist/"]
