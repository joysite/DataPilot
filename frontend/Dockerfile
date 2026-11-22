# 第一阶段：构建 Vue 前端
FROM node:24-alpine AS builder

WORKDIR /app

# 优先复制依赖清单，利用 Docker 构建缓存
COPY frontend/package.json frontend/package-lock.json ./

RUN npm ci

# 复制前端源码并构建
COPY frontend/ ./

RUN npm run build


# 第二阶段：Nginx 静态托管
FROM nginx:alpine

COPY frontend/nginx.conf /etc/nginx/conf.d/default.conf
COPY --from=builder /app/dist /usr/share/nginx/html

EXPOSE 80

CMD ["nginx", "-g", "daemon off;"]
