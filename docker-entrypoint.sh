#!/usr/bin/env bash
set -euo pipefail

DATA_DIR=/app/backend/data
LOG_DIR=/app/backend/logs

# 容器以 root 启动：先确保挂载卷可写，再降权到非 root 用户 anyrouter 运行。
# 若 compose 里显式指定了 user:，则已是非 root，直接执行。
if [ "$(id -u)" = "0" ]; then
    mkdir -p "${DATA_DIR}" "${LOG_DIR}"

    # bind mount 首次由 docker 以 root 创建，属主不对时递归修正一次。
    # 顶层目录属主已正确就跳过，避免每次启动都 chown 整个数据目录。
    for dir in "${DATA_DIR}" "${LOG_DIR}"; do
        if [ "$(stat -c '%U' "${dir}" 2>/dev/null || echo unknown)" != "anyrouter" ]; then
            chown -R anyrouter:anyrouter "${dir}" 2>/dev/null || true
        fi
    done

    exec gosu anyrouter "$@"
fi

exec "$@"
