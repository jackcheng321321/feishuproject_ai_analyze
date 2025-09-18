# AI综合分析管理平台 - 前端生产环境Dockerfile
# 多阶段构建：构建阶段 + 运行阶段

# 第一阶段：构建Vue应用
FROM node:18-alpine AS builder

# 设置工作目录
WORKDIR /app

# 设置环境变量
ENV NODE_ENV=production

# 安装系统依赖
RUN apk add --no-cache git

# 复制package文件并安装依赖
COPY package*.json ./
RUN npm ci --only=production

# 复制源代码
COPY . .

# 构建生产版本
RUN npm run build

# 第二阶段：Nginx运行环境
FROM nginx:alpine AS runtime

# 创建非root用户
RUN addgroup -g 1001 -S nginx-user && \
    adduser -S -D -H -u 1001 -h /var/cache/nginx -s /sbin/nologin -G nginx-user -g nginx-user nginx-user

# 从构建阶段复制构建结果
COPY --from=builder /app/dist /usr/share/nginx/html

# 创建Nginx配置
COPY --from=builder /app/nginx.conf /etc/nginx/nginx.conf

# 如果没有nginx.conf，创建默认配置
RUN if [ ! -f /etc/nginx/nginx.conf ]; then \
    echo 'events { worker_connections 1024; }' > /etc/nginx/nginx.conf && \
    echo 'http {' >> /etc/nginx/nginx.conf && \
    echo '  include /etc/nginx/mime.types;' >> /etc/nginx/nginx.conf && \
    echo '  default_type application/octet-stream;' >> /etc/nginx/nginx.conf && \
    echo '  sendfile on;' >> /etc/nginx/nginx.conf && \
    echo '  keepalive_timeout 65;' >> /etc/nginx/nginx.conf && \
    echo '  gzip on;' >> /etc/nginx/nginx.conf && \
    echo '  server {' >> /etc/nginx/nginx.conf && \
    echo '    listen 80;' >> /etc/nginx/nginx.conf && \
    echo '    server_name localhost;' >> /etc/nginx/nginx.conf && \
    echo '    root /usr/share/nginx/html;' >> /etc/nginx/nginx.conf && \
    echo '    index index.html;' >> /etc/nginx/nginx.conf && \
    echo '    location / {' >> /etc/nginx/nginx.conf && \
    echo '      try_files $uri $uri/ /index.html;' >> /etc/nginx/nginx.conf && \
    echo '    }' >> /etc/nginx/nginx.conf && \
    echo '    location /api/ {' >> /etc/nginx/nginx.conf && \
    echo '      proxy_pass http://backend:8000/api/;' >> /etc/nginx/nginx.conf && \
    echo '      proxy_set_header Host $host;' >> /etc/nginx/nginx.conf && \
    echo '      proxy_set_header X-Real-IP $remote_addr;' >> /etc/nginx/nginx.conf && \
    echo '      proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;' >> /etc/nginx/nginx.conf && \
    echo '      proxy_set_header X-Forwarded-Proto $scheme;' >> /etc/nginx/nginx.conf && \
    echo '    }' >> /etc/nginx/nginx.conf && \
    echo '    error_page 404 /index.html;' >> /etc/nginx/nginx.conf && \
    echo '  }' >> /etc/nginx/nginx.conf && \
    echo '}' >> /etc/nginx/nginx.conf; \
    fi

# 设置正确的权限
RUN chown -R nginx-user:nginx-user /usr/share/nginx/html && \
    chown -R nginx-user:nginx-user /var/cache/nginx && \
    chown -R nginx-user:nginx-user /var/log/nginx && \
    chown -R nginx-user:nginx-user /etc/nginx/conf.d

# 修改nginx.conf权限
RUN chmod 644 /etc/nginx/nginx.conf

# 创建pid文件目录
RUN mkdir -p /var/run/nginx && \
    chown -R nginx-user:nginx-user /var/run/nginx

# 切换到非root用户
USER nginx-user

# 暴露端口
EXPOSE 80

# 健康检查
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD wget --no-verbose --tries=1 --spider http://localhost/ || exit 1

# 启动Nginx
CMD ["nginx", "-g", "daemon off;"]