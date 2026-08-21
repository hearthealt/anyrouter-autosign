# 部署文档

## 目录

- [本地部署](#本地部署)
- [Docker 部署](#docker-部署)
- [升级](#升级)
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

# 开发环境读取仓库根目录的 .env（首次先 cp .env.example .env）
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

推荐方式。前端构建产物打进同一个镜像、由后端直接提供，只有一个应用容器，不需要额外的 nginx。

镜像由 GitHub Actions 自动构建并推送到 GHCR：`ghcr.io/hearthealt/anyrouter-autosign`。

### 1. 准备部署目录

```bash
mkdir -p /opt/anyrouter && cd /opt/anyrouter

# 只需要这两个文件，不用克隆整个仓库
curl -O https://raw.githubusercontent.com/hearthealt/anyrouter-autosign/master/docker-compose.yml
curl -o .env https://raw.githubusercontent.com/hearthealt/anyrouter-autosign/master/.env.example
```

### 2. 修改 .env

```bash
# 生成两个随机密钥
openssl rand -hex 32   # 填入 JWT_SECRET_KEY
openssl rand -hex 32   # 填入 WATCHTOWER_HTTP_API_TOKEN

vi .env
```

必须设置的三项：

| 变量 | 说明 |
|---|---|
| `JWT_SECRET_KEY` | JWT 签名密钥。不改等于没有鉴权 |
| `DEFAULT_ADMIN_PASSWORD` | 首次启动创建的管理员密码 |
| `WATCHTOWER_HTTP_API_TOKEN` | 页面「更新并重启」用的令牌，留空则更新按钮不可用 |

> 仓库还没有打过 `v*` tag 时 `:latest` 不存在，先在 `.env` 里改成
> `ANYROUTER_IMAGE=ghcr.io/hearthealt/anyrouter-autosign:edge`（每次推送 master 都会更新）。

### 3. 启动

```bash
docker compose up -d
docker compose logs -f app
```

访问 `http://<服务器IP>:16168`，用 `.env` 里的管理员账号登录。

### 目录与端口

| 项 | 值 |
|---|---|
| 应用端口 | `16168`（改 `.env` 的 `ANYROUTER_PORT`，容器内也是 16168） |
| 数据库 | `./data/anyrouter.db` |
| 日志 | `./logs/` |
| watchtower | 只监听 `127.0.0.1:8081`，不对外暴露 |

`data/` 和 `logs/` 是 bind mount，容器重建不会丢数据。**升级前请先备份 `data/`。**

### 关于 watchtower

`docker-compose.yml` 里的 watchtower 用 `--interval 0` 启动，**不做定时轮询**，只响应页面上「更新并重启」的手动触发。

`/var/run/docker.sock` 只挂在 watchtower 上，应用容器本身没有任何宿主机 Docker 权限。

不需要一键更新的话，可以整个删掉 watchtower 服务，用下面的手动升级方式。

---

## 升级

### 方式一：页面一键更新

设置 → 关于 → 检查更新 → 更新并重启。

页面会调用 watchtower 拉取新镜像、重建容器，等服务恢复后自动刷新。整个过程服务中断约 10-30 秒。

前提是 `.env` 里配置了 `WATCHTOWER_HTTP_API_TOKEN`，且 watchtower 容器在运行。

### 方式二：命令行

```bash
cd /opt/anyrouter
docker compose pull
docker compose up -d
docker image prune -f
```

### 版本号

版本号以仓库根目录的 `VERSION` 文件为唯一来源，构建时打进镜像。
「检查更新」会读取 GitHub 上 master 分支的 `VERSION` 和 `CHANGELOG.md` 做对比。

不要在 `.env` 里设置 `APP_VERSION` —— 环境变量优先级更高，会盖住镜像里的真实版本号。

### 镜像标签

| 标签 | 产生时机 |
|---|---|
| `latest` | 推送 `v*` tag 时 |
| `edge` | 每次推送 master 时 |
| `1.1.0` / `1.1` | 推送 `v1.1.0` tag 时 |
| `sha-xxxxxxx` | 每次构建 |

镜像目前只构建 `linux/amd64`。ARM 机器需要自行构建，或修改 workflow 里的 `platforms`。

---

## 生产环境部署

### 1. 后端部署

#### 使用 Gunicorn

```bash
cd backend
pip install gunicorn

ENVIRONMENT=production gunicorn app.main:app \
  --workers 1 \
  --worker-class uvicorn.workers.UvicornWorker \
  --bind 0.0.0.0:8000
```

说明：

- `requirements.txt` 已包含 `uvicorn[standard]`，但不包含 `gunicorn`
- 如果你使用 Gunicorn 作为生产入口，需要额外安装 `gunicorn`
- **当前 APScheduler 随 Web 进程启动，不支持多 Worker。必须保持 `--workers 1`，否则每个 Worker 都会重复执行定时签到和健康检查**
- 需要多 Worker 承载 API 时，应先把调度器拆成独立进程，或实现可靠的分布式锁

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
  --workers 1 \
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

全项目只有一个配置文件：**仓库根目录的 `.env`**（模板见 `.env.example`）。

- 优先级：系统环境变量 > 根目录 `.env` > 代码默认值
- 这一个文件同时被两处读取：`docker compose` 的 `${...}` 变量替换，以及后端的 pydantic settings
- Docker 部署时 `.env` 不进镜像，应用配置由 `docker-compose.yml` 的 `environment` 注入
- `ENVIRONMENT` **不能**写在 `.env` 里 —— 它在模块导入时就要用到，早于 `.env` 被读取，只能通过系统环境变量设置（镜像里已固定为 `production`，本地默认 `development`）
- 同理不要设置 `APP_VERSION`，版本号以根目录 `VERSION` 文件为唯一来源

### 常用环境变量

| 变量名 | 说明 | 默认值 |
|--------|------|--------|
| `ANYROUTER_PORT` | 宿主机映射端口（仅 docker compose 用） | `16168` |
| `ANYROUTER_IMAGE` | 镜像地址（仅 docker compose 用） | `ghcr.io/hearthealt/anyrouter-autosign:latest` |
| `JWT_SECRET_KEY` | JWT 签名密钥，**必改** | 代码内置的占位值 |
| `WATCHTOWER_HTTP_API_TOKEN` | 一键更新令牌，留空则更新按钮不可用 | 空 |
| `APP_NAME` | 应用名称 | `AnyRouter Admin` |
| `DEBUG` | 是否开启调试 | `false` |
| `DATABASE_URL` | 数据库连接字符串 | `sqlite:///./data/anyrouter.db` |
| `LOG_LEVEL` / `LOG_FORMAT` / `LOG_DIR` | 日志级别 / 格式（`text`\|`json`）/ 目录 | `INFO` / `text` / `./logs` |
| `REQUEST_TIMEOUT` | 请求超时秒数 | `30` |
| `RETRY_TIMES` | 重试次数 | `3` |
| `RETRY_INTERVAL` | 重试间隔秒数 | `3` |
| `DEFAULT_ADMIN_USERNAME` | 默认管理员用户名 | `admin` |
| `DEFAULT_ADMIN_PASSWORD` | 默认管理员密码，**必改** | `admin123` |

> `DATABASE_URL` 和 `LOG_DIR` 里的相对路径是相对**进程工作目录**（`backend/`，容器内为 `/app/backend`）。

说明：

- 全局平台代理环境变量已移除
- 如需代理访问目标平台，请在账号编辑中把“访问出口”设置为“自定义代理”
- 账号级代理仅作用于该账号访问目标平台的请求，不影响浏览器访问前端页面

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

- 如果服务器所在网络无法直连目标平台，可在账号编辑中把“访问出口”设置为“自定义代理”
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
