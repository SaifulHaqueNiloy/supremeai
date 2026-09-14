# Multi-stage Dockerfile for Frontend (Vite + React)
FROM node:20-alpine AS builder
WORKDIR /app

# Enable corepack for pnpm if needed, or use npm
RUN corepack enable && corepack prepare pnpm@latest --activate

# Copy root and package files for monorepo / workspace dependencies
COPY package.json pnpm-lock.yaml* pnpm-workspace.yaml* ./
COPY frontend/package.json ./frontend/
COPY packages/ ./packages/

# Install dependencies
RUN pnpm install --frozen-lockfile || pnpm install

# Copy frontend source code
COPY frontend/ ./frontend/

# Build frontend
WORKDIR /app/frontend
# FINAL-TEST P0 FIX (frontend/backend URL contract):
# Vite inlines VITE_* at build time. Previously this file defaulted
# VITE_API_URL to http://localhost:8080, so any production build that forgot
# the real backend URL silently shipped a bundle calling localhost (degraded
# viewer mode in production). The default is now EMPTY and
# scripts/validate-build-env.mjs HARD-FAILS the build unless a real backend
# URL is provided (or VITE_USE_RELATIVE_PATH=true for same-host proxy deploys,
# or the explicit local-testing escape hatch VITE_ALLOW_LOCAL_BACKEND=true).
ARG VITE_API_URL
ARG VITE_USER_BACKEND
ARG VITE_ADMIN_BACKEND
ARG VITE_USE_RELATIVE_PATH
ARG VITE_ALLOW_LOCAL_BACKEND
ENV VITE_API_URL=$VITE_API_URL \
    VITE_BACKEND_URL=$VITE_API_URL \
    VITE_USER_BACKEND=$VITE_USER_BACKEND \
    VITE_ADMIN_BACKEND=$VITE_ADMIN_BACKEND \
    VITE_USE_RELATIVE_PATH=$VITE_USE_RELATIVE_PATH \
    VITE_ALLOW_LOCAL_BACKEND=$VITE_ALLOW_LOCAL_BACKEND \
    NODE_ENV=production

RUN pnpm run build

# Stage 2: Serve with lightweight Nginx
FROM nginx:alpine AS runtime
COPY --from=builder /app/frontend/dist /usr/share/nginx/html
COPY frontend/nginx.conf /etc/nginx/conf.d/default.conf

# Setup non-root execution permissions for nginx user
RUN chown -R nginx:nginx /usr/share/nginx/html \
    && chmod -R 755 /usr/share/nginx/html \
    && chown -R nginx:nginx /var/cache/nginx \
    && chown -R nginx:nginx /var/log/nginx \
    && chown -R nginx:nginx /etc/nginx/conf.d \
    && touch /var/run/nginx.pid \
    && chown -R nginx:nginx /var/run/nginx.pid

USER nginx

EXPOSE 80
CMD ["nginx", "-g", "daemon off;"]

