# 更新日志

## 1.1.1

+ [修复] 为 Watchtower 显式设置 Docker API 1.40，兼容 Docker Engine 最低 API 为 1.40 的服务器
+ [优化] 通过 Watchtower scope 隔离本项目，避免与同机其它项目互相更新
+ [优化] 移除 Watchtower 宿主机端口映射，仅通过 Compose 内部网络提供更新接口
+ [新增] 推送版本 tag 时自动创建 GitHub Release，并附带镜像拉取命令
## 1.1.0

+ [新增] Docker 单容器部署：前端构建产物由后端直接提供，一条 `docker compose up -d` 起服务
+ [新增] 推送 `master` 或 `v*` tag 自动构建并发布镜像到 GitHub Container Registry
+ [新增] 设置页「关于」标签：展示当前版本、检查云端新版本、一键更新并重启
+ [新增] 侧边栏底部显示版本号，有新版本时提示
+ [优化] 平台 Base URL 在平台管理、账号管理、签到记录、账号详情、总览面板中均可直接点击跳转
+ [优化] 版本号统一以仓库根目录 `VERSION` 文件为唯一来源
