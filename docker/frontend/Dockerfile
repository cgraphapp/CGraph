FROM node:18-alpine AS builder

WORKDIR /app

# Install dependencies
COPY frontend/package*.json .
RUN npm ci

# Build
COPY frontend/ .
RUN npm run build

# Nginx stage
FROM nginx:alpine

COPY --from=builder /app/build /usr/share/nginx/html
COPY docker/frontend/nginx.conf /etc/nginx/conf.d/default.conf

EXPOSE 80

CMD ["nginx", "-g", "daemon off;"]
