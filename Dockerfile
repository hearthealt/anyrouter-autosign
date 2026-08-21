# ---------- 前端构建 ----------
FROM node:22-alpine AS web-build

WORKDIR /app/frontend

COPY frontend/package.json frontend/package-lock.json ./
RUN npm ci

COPY frontend/ ./
# package.json 的 build 是 `vue-tsc -b && vite build`，类型错误会直接中断镜像构建
RUN npm run build


# ---------- 运行时 ----------
# 基础镜像固定 3.11：backend/requirements.txt 里的 pydantic==2.5.3 / aiohttp==3.9.1 等
# 固定版本没有 cp313 的预编译 wheel，在 3.13 上会退化成源码编译（需要 Rust/gcc）。
FROM python:3.11-slim-bookworm AS app

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    ENVIRONMENT=production \
    TZ=Asia/Shanghai

WORKDIR /app/backend

# curl          HEALTHCHECK 用
# gosu          entrypoint 修正数据卷属主后降权
# tzdata        容器内时区（调度器按 Asia/Shanghai 算签到时间）
# libglib2.0-0  ddddocr 依赖的 opencv-python-headless 需要
# libgomp1      ddddocr 依赖的 onnxruntime 需要 OpenMP 运行时
RUN apt-get update && apt-get install -y --no-install-recommends \
        curl \
        gosu \
        tzdata \
        libglib2.0-0 \
        libgomp1 \
    && rm -rf /var/lib/apt/lists/*

RUN groupadd -r anyrouter && useradd -r -g anyrouter -u 1000 anyrouter

COPY backend/requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

# VERSION 落在 /app，与仓库结构一致：config.py 的 BASE_DIR 是 /app/backend，
# 因此 BASE_DIR.parent / "VERSION" 在容器内外都能命中同一个文件。
COPY VERSION /app/VERSION
COPY backend/app ./app
COPY docker-entrypoint.sh /usr/local/bin/docker-entrypoint.sh
COPY --from=web-build /app/frontend/dist /app/web

RUN chmod +x /usr/local/bin/docker-entrypoint.sh \
    && mkdir -p /app/backend/data /app/backend/logs \
    && chown -R anyrouter:anyrouter /app

EXPOSE 16168

HEALTHCHECK --interval=30s --timeout=5s --start-period=40s --retries=3 \
    CMD curl -fsS http://localhost:16168/health || exit 1

ENTRYPOINT ["docker-entrypoint.sh"]
# 不要加 --workers：APScheduler 在进程内调度，多 worker 会让每个定时签到重复执行
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "16168"]
