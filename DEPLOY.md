# 部署文档

## 目录

- [本地部署](#本地部署)
- [Docker 部署](#docker-部署)
- [生产环境部署](#生产环境部署)
- [Nginx 配置](#nginx-配置)
- [常见问题](#常见问题)

---

## 本地部署

### 1. 克隆项目

```bash
git clone https://github.com/your-repo/anyrouter-autolog.git
cd anyrouter-autolog
```

### 2. 启动后端

```bash
cd backend

# 创建虚拟环境
python -m venv venv

# 激活虚拟环境
# Windows
venv\Scripts\activate
# Linux/macOS
source venv/bin/activate

# 安装依赖
pip install -r requirements.txt

# 创建数据目录
mkdir -p data

# 启动服务
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

### 3. 启动前端

```bash
cd frontend

# 安装依赖
pnpm install
# 或
npm install

# 开发模式启动
pnpm dev
```

### 4. 访问

- 前端：http://localhost:3000
- 后端 API：http://localhost:8000
- Swagger 文档：http://localhost:8000/docs

---

## Docker 部署

### 创建 Dockerfile

**backend/Dockerfile**

```dockerfile
FROM python:3.11-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

RUN mkdir -p /app/data

EXPOSE 8000

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
```

**frontend/Dockerfile**

```dockerfile
FROM node:18-alpine as builder

WORKDIR /app

COPY package.json pnpm-lock.yaml ./
RUN npm install -g pnpm && pnpm install

COPY . .
RUN pnpm build

FROM nginx:alpine
COPY --from=builder /app/dist /usr/share/nginx/html
COPY nginx.conf /etc/nginx/conf.d/default.conf

EXPOSE 80
```

### docker-compose.yml

```yaml
version: '3.8'

services:
  backend:
    build: ./backend
    ports:
      - "8000:8000"
    volumes:
      - ./data:/app/data
    environment:
      - DATABASE_URL=sqlite:///./data/anyrouter.db
    restart: unless-stopped

  frontend:
    build: ./frontend
    ports:
      - "80:80"
    depends_on:
      - backend
    restart: unless-stopped
```

### 启动

```bash
docker-compose up -d
```

---

## 生产环境部署

### 1. 后端部署

#### 使用 Gunicorn

```bash
pip install gunicorn

gunicorn app.main:app \
  --workers 4 \
  --worker-class uvicorn.workers.UvicornWorker \
  --bind 0.0.0.0:8000
```

#### 使用 systemd 服务

创建 `/etc/systemd/system/anyrouter-admin.service`：

```ini
[Unit]
Description=AnyRouter Admin Backend
After=network.target

[Service]
Type=simple
User=www-data
WorkingDirectory=/opt/anyrouter-autolog/backend
Environment="PATH=/opt/anyrouter-autolog/backend/venv/bin"
ExecStart=/opt/anyrouter-autolog/backend/venv/bin/gunicorn app.main:app \
  --workers 4 \
  --worker-class uvicorn.workers.UvicornWorker \
  --bind 127.0.0.1:8000
Restart=always

[Install]
WantedBy=multi-user.target
```

启动服务：

```bash
sudo systemctl daemon-reload
sudo systemctl enable anyrouter-admin
sudo systemctl start anyrouter-admin
```

### 2. 前端构建

```bash
cd frontend
pnpm build
```

构建产物在 `dist/` 目录，部署到 Web 服务器即可。

---

## Nginx 配置

### 前后端分离部署

```nginx
server {
    listen 80;
    server_name your-domain.com;

    # 前端静态文件
    location / {
        root /opt/anyrouter-autolog/frontend/dist;
        index index.html;
        try_files $uri $uri/ /index.html;
    }

    # 后端 API 代理
    location /api {
        proxy_pass http://127.0.0.1:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }

    # 后端文档
    location /docs {
        proxy_pass http://127.0.0.1:8000;
        proxy_set_header Host $host;
    }

    location /openapi.json {
        proxy_pass http://127.0.0.1:8000;
        proxy_set_header Host $host;
    }
}
```

### 启用 HTTPS

```nginx
server {
    listen 80;
    server_name your-domain.com;
    return 301 https://$server_name$request_uri;
}

server {
    listen 443 ssl http2;
    server_name your-domain.com;

    ssl_certificate /path/to/cert.pem;
    ssl_certificate_key /path/to/key.pem;

    # ... 其他配置同上
}
```

---

## 环境变量

| 变量名 | 说明 | 默认值 |
|--------|------|--------|
| `APP_NAME` | 应用名称 | AnyRouter Admin |
| `DEBUG` | 调试模式 | true |
| `DATABASE_URL` | 数据库连接 | sqlite:///./data/anyrouter.db |
| `REQUEST_TIMEOUT` | 请求超时(秒) | 30 |
| `RETRY_TIMES` | 重试次数 | 3 |

在 `backend/.env` 文件中配置：

```env
APP_NAME=AnyRouter Admin
DEBUG=false
DATABASE_URL=sqlite:///./data/anyrouter.db
```

---

## 常见问题

### 1. 数据库文件位置

默认在 `backend/data/anyrouter.db`，确保目录存在且有写入权限：

```bash
mkdir -p backend/data
chmod 755 backend/data
```

### 2. 签到失败

- 检查账号的 session_cookie 是否过期
- 检查 user_id 是否正确
- 查看后端日志排查问题

### 3. 定时任务不执行

- 确认已在设置中开启自动签到
- 检查后端服务是否正常运行
- 查看日志确认调度器状态

### 4. 前端无法访问后端

- 开发环境：检查 vite.config.ts 中的代理配置
- 生产环境：检查 Nginx 反向代理配置

### 5. 跨域问题

后端已配置 CORS 允许所有来源，如需限制，修改 `backend/app/main.py`：

```python
app.add_middleware(
    CORSMiddleware,
    allow_origins=["https://your-domain.com"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
```

---

## 数据备份

### SQLite 备份

```bash
# 备份
cp backend/data/anyrouter.db backend/data/anyrouter.db.backup

# 恢复
cp backend/data/anyrouter.db.backup backend/data/anyrouter.db
```

### 定时备份脚本

```bash
#!/bin/bash
BACKUP_DIR="/opt/backups/anyrouter"
DATE=$(date +%Y%m%d_%H%M%S)

mkdir -p $BACKUP_DIR
cp /opt/anyrouter-autolog/backend/data/anyrouter.db $BACKUP_DIR/anyrouter_$DATE.db

# 保留最近 7 天的备份
find $BACKUP_DIR -name "anyrouter_*.db" -mtime +7 -delete
```

添加到 crontab：

```bash
0 2 * * * /opt/scripts/backup-anyrouter.sh
```
