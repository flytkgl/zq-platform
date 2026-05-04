FROM node:20-alpine AS builder

ARG VITE_GLOB_API_URL=/basic-api
ARG VITE_APP_TITLE=ZQ-Platform
ARG VITE_APP_NAMESPACE=vben-web-ele

ENV VITE_GLOB_API_URL=$VITE_GLOB_API_URL \
    VITE_APP_TITLE=$VITE_APP_TITLE \
    VITE_APP_NAMESPACE=$VITE_APP_NAMESPACE

WORKDIR /app

RUN npm install -g pnpm@9 --registry=https://registry.npmmirror.com

COPY web/ .

RUN pnpm install --frozen-lockfile --prefer-offline

RUN pnpm run build --filter=@vben/web-ele

FROM nginx:alpine

RUN apk add --no-cache curl

COPY docker/nginx/nginx.conf /etc/nginx/nginx.conf
COPY docker/nginx/conf.d/ /etc/nginx/conf.d/

COPY --from=builder /app/apps/web-ele/dist /usr/share/nginx/html

EXPOSE 80

HEALTHCHECK --interval=30s --timeout=3s --start-period=10s --retries=3 \
    CMD curl -f http://localhost/ || exit 1

CMD ["nginx", "-g", "daemon off;"]
