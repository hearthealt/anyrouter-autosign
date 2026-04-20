# 部署文档

## 目录

- [本地部署](#本地部署)
- [Docker 部署](#docker-部署)
- [生产环境部署](#生产环境部署)
- [Nginx 配置](#nginx-配置)
- [环境变量与配置文件](#环境变量与配置文件)
- [数据库迁移说明](#数据库迁移说明)
- [常见问题](#常见问题)
- [数据备份](#数据备份)

---

## 本地部署

### 1. 克隆项目

```bash
git clone https://github.com/hearthealt/anyrouter-autosign.git
cd anyrouter-autosign
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
mkdir data

# 开发环境会默认读取 backend/.env.local
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

### 3. 启动前端

```bash
cd frontend

# 安装依赖
npm install
# 或
pnpm install

# 开发模式启动
npm run dev
# 或
pnpm dev
```

### 4. 访问

- 前端：http://localhost:3000
- 后端 API：http://localhost:8000
- Swagger 文档：http://localhost:8000/docs

---

## Docker 部署

以下内容为示例，需要你自行创建对应文件。

### backend/Dockerfile

```dockerfile
FROM python:3.11-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

RUN mkdir -p /app/data

ENV ENVIRONMENT=production

EXPOSE 8000

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
```

### frontend/Dockerfile

```dockerfile
FROM node:20-alpine AS builder

WORKDIR /app

COPY package.json package-lock.json ./
RUN npm install

COPY . .
RUN npm run build

FROM nginx:alpine
COPY --from=builder /app/dist /usr/share/nginx/html
COPY nginx.conf /etc/nginx/conf.d/default.conf

EXPOSE 80
```

### frontend/nginx.conf

```nginx
server {
    listen 80;
    server_name _;

    root /usr/share/nginx/html;
    index index.html;

    location / {
        try_files $uri $uri/ /index.html;
    }

    location /api {
        proxy_pass http://backend:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }

    location /api/v1/events {
        proxy_pass http://backend:8000;
        proxy_http_version 1.1;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        proxy_set_header Connection "";
        proxy_buffering off;
        proxy_read_timeout 3600s;
    }
}
```

### docker-compose.yml

```yaml
version: "3.8"

services:
  backend:
    build: ./backend
    ports:
      - "8000:8000"
    volumes:
      - ./data:/app/data
    environment:
      ENVIRONMENT: production
      DATABASE_URL: sqlite:///./data/anyrouter.db
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
docker compose up -d
```

---

## 生产环境部署

### 1. 后端部署

#### 使用 Gunicorn

```bash
cd backend
pip install gunicorn

ENVIRONMENT=production gunicorn app.main:app \
  --workers 4 \
  --worker-class uvicorn.workers.UvicornWorker \
  --bind 0.0.0.0:8000
```

说明：

- `requirements.txt` 已包含 `uvicorn[standard]`，但不包含 `gunicorn`
- 如果你使用 Gunicorn 作为生产入口，需要额外安装 `gunicorn`

#### 使用 systemd 服务

创建 `/etc/systemd/system/anyrouter-admin.service`：

```ini
[Unit]
Description=AnyRouter Admin Backend
After=network.target

[Service]
Type=simple
User=www-data
WorkingDirectory=/opt/anyrouter-autosign/backend
Environment="PATH=/opt/anyrouter-autosign/backend/venv/bin"
Environment="ENVIRONMENT=production"
ExecStart=/opt/anyrouter-autosign/backend/venv/bin/gunicorn app.main:app \
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
npm install
npm run build
```

如果你使用 `pnpm`，可替换为 `pnpm install` 和 `pnpm build`。

构建产物在 `frontend/dist/` 目录，部署到 Web 服务器即可。

代码升级说明：

- 后端改动只需要重启后端服务即可生效
- 前端界面改动（例如账号页首屏加载态）需要重新执行 `npm run build` 并发布新的 `frontend/dist/`

---

## Nginx 配置

### 前后端分离部署

```nginx
server {
    listen 80;
    server_name your-domain.com;

    location / {
        root /opt/anyrouter-autosign/frontend/dist;
        index index.html;
        try_files $uri $uri/ /index.html;
    }

    location /api {
        proxy_pass http://127.0.0.1:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }

    location /api/v1/events {
        proxy_pass http://127.0.0.1:8000;
        proxy_http_version 1.1;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        proxy_set_header Connection "";
        proxy_buffering off;
        proxy_read_timeout 3600s;
    }

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

    location / {
        root /opt/anyrouter-autosign/frontend/dist;
        index index.html;
        try_files $uri $uri/ /index.html;
    }

    location /api {
        proxy_pass http://127.0.0.1:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }

    location /api/v1/events {
        proxy_pass http://127.0.0.1:8000;
        proxy_http_version 1.1;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        proxy_set_header Connection "";
        proxy_buffering off;
        proxy_read_timeout 3600s;
    }
}
```

SSE 说明：

- `/api/v1/events` 使用的是 SSE 长连接，不是 WebSocket
- 不要为该路径额外添加 `Upgrade` / `Connection: upgrade` 头
- 如果你把 HTTPS 请求直接打到后端的 HTTP 端口，或把 SSE 当成 WebSocket 代理，后端日志里可能出现 `Invalid HTTP request received` 或 `Unsupported upgrade request`

---

## 环境变量与配置文件

### 加载规则

- 默认环境为 `development`
- `ENVIRONMENT=development` 时，后端读取 `backend/.env.local`
- `ENVIRONMENT=production` 时，后端读取 `backend/.env.production`
- 系统环境变量优先于文件中的同名配置
- 当前仓库保留 `backend/.env.production.example` 作为生产示例
- 开发环境请自行创建 `backend/.env.local`，字段可参考 `backend/.env.production.example`

### 常用环境变量

| 变量名 | 说明 | 默认值 |
|--------|------|--------|
| `ENVIRONMENT` | 运行环境，`development` 或 `production` | `development` |
| `APP_NAME` | 应用名称 | `AnyRouter Admin` |
| `DEBUG` | 是否开启调试 | `false` |
| `DATABASE_URL` | 数据库连接字符串 | `sqlite:///./data/anyrouter.db` |
| `REQUEST_TIMEOUT` | 请求超时秒数 | `30` |
| `RETRY_TIMES` | 重试次数 | `3` |
| `RETRY_INTERVAL` | 重试间隔秒数 | `3` |
| `ANYROUTER_PROXY_ENABLED` | 后端平台代理默认开关 | `false` |
| `ANYROUTER_PROXY_URL` | 后端平台代理地址 | 空 |
| `DEFAULT_ADMIN_USERNAME` | 默认管理员用户名 | `admin` |
| `DEFAULT_ADMIN_PASSWORD` | 默认管理员密码 | `admin123` |

### 生产环境示例

`backend/.env.production`

```env
DEBUG=false
DATABASE_URL=sqlite:///./data/anyrouter.db
ANYROUTER_PROXY_ENABLED=false
ANYROUTER_PROXY_URL=
DEFAULT_ADMIN_USERNAME=admin
DEFAULT_ADMIN_PASSWORD=admin123
```

说明：

- `ANYROUTER_PROXY_ENABLED` 和 `ANYROUTER_PROXY_URL` 是后端启动时的默认值
- 如果你已经在前端「系统设置」页面保存了代理配置，运行时会优先使用页面保存的配置
- 代理仅作用于后端访问目标平台的请求，不影响浏览器访问前端页面

---

## 数据库迁移说明

后端启动时会自动执行数据库初始化和兼容迁移，无需手动改表。当前版本会自动处理以下内容：

- 如果没有平台数据，会自动创建默认平台 `AnyRouter`
- 旧版数据库缺少 `accounts.platform_id` 时，会自动补列并把旧账号回填到默认平台
- 旧版数据库缺少 `platforms.checkin_api` 时，会自动补列并回填默认值 `/api/user/checkin`
- 如果默认平台被删除后仍有其它平台，系统会自动提升最早创建的平台为新的默认平台

生产环境升级前，仍然建议先备份数据库文件。

---

## 常见问题

### 1. 数据库文件位置

默认在 `backend/data/anyrouter.db`，确保目录存在且有写入权限：

```bash
cd backend
mkdir data
```

### 2. 签到失败

- 检查账号的 `session_cookie` 是否过期
- 检查 `user_id` 是否正确
- 检查账号关联的平台接口路径是否填写正确，尤其是 `sign_api` 和 `checkin_api`
- 查看后端日志排查问题

### 3. 无法访问目标平台或请求超时

- 如果服务器所在网络无法直连目标平台，可在「系统设置」中开启后端平台代理
- 代理地址需填写 `http://` 或 `https://` 格式
- 如果使用带认证代理，确认用户名和密码正确
- 查看后端日志确认是否为代理连接失败、超时或认证失败

### 4. 定时任务不执行

- 确认已在设置中开启自动签到
- 检查后端服务是否正常运行
- 查看日志确认调度器状态

### 5. 签到成功后额度没有立即更新

- 新版本会在单账号签到、批量签到、自动签到和重试签到完成后自动同步账号缓存额度
- 如果你刚升级后端但页面仍显示旧额度，先确认后端服务已重启
- 如果账号页仍出现旧的前端行为，请重新构建并发布前端静态资源
- 如果同步仍失败，检查后端日志中是否存在获取用户信息失败、`session_cookie` 失效或目标平台接口异常

### 6. 账号页先显示“没有账号”再出现数据

- 新版本账号页首屏会优先显示加载状态，不会在请求返回前先闪空状态
- 如果线上仍出现旧表现，通常是前端静态资源还没有重新构建或浏览器缓存了旧文件
- 重新执行前端构建并发布 `frontend/dist/` 后再刷新页面

### 7. 后端日志出现 `Invalid HTTP request received` 或 `Unsupported upgrade request`

- 先确认浏览器和反向代理访问的是 Nginx 的 80/443，而不是直接访问后端 HTTP 端口
- 确认 `/api/v1/events` 按 SSE 转发，不要加 WebSocket Upgrade 头
- 如果后端端口直接暴露公网，被扫描器探测时也可能出现这类日志
- 一般不影响业务接口本身，但建议把后端只监听在内网地址，再由 Nginx 对外提供访问

### 8. 前端无法访问后端

- 开发环境：检查 `frontend/vite.config.ts`，如果你使用的是 JS 配置文件则检查 `frontend/vite.config.js`
- 生产环境：检查 Nginx 反向代理配置

### 9. 跨域问题

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
cp /opt/anyrouter-autosign/backend/data/anyrouter.db $BACKUP_DIR/anyrouter_$DATE.db

find $BACKUP_DIR -name "anyrouter_*.db" -mtime +7 -delete
```

添加到 crontab：

```bash
0 2 * * * /opt/scripts/backup-anyrouter.sh
```
