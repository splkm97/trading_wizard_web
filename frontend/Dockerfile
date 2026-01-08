# Trading Wizard Web - Frontend Dockerfile
# Stage 1: Build
FROM node:20-alpine AS builder

WORKDIR /app

# Copy package files
COPY package.json package-lock.json* ./
RUN npm ci

# Copy source files
COPY . .

# Build
RUN npm run build

# Stage 2: Production
FROM nginx:alpine

# Copy nginx config template
COPY nginx.conf.template /etc/nginx/nginx.conf.template

# Copy built assets
COPY --from=builder /app/dist /usr/share/nginx/html

# Expose port
EXPOSE 80

# Default backend URL (can be overridden by environment variable)
ENV BACKEND_URL=http://backend:8000

# Use envsubst to replace environment variables at runtime
CMD ["/bin/sh", "-c", "envsubst '${BACKEND_URL}' < /etc/nginx/nginx.conf.template > /etc/nginx/nginx.conf && nginx -g 'daemon off;'"]
