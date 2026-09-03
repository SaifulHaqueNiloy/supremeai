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
ARG VITE_API_URL=http://localhost:8080
ENV VITE_API_URL=$VITE_API_URL \
    VITE_BACKEND_URL=$VITE_API_URL \
    VITE_USER_BACKEND=$VITE_API_URL \
    VITE_ADMIN_BACKEND=$VITE_API_URL \
    NODE_ENV=production

RUN pnpm run build

# Stage 2: Serve with lightweight Nginx
FROM nginx:alpine AS runtime
COPY --from=builder /app/frontend/dist /usr/share/nginx/html
COPY frontend/nginx.conf /etc/nginx/conf.d/default.conf

EXPOSE 80
CMD ["nginx", "-g", "daemon off;"]
