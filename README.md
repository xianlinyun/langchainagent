# 一键部署指南

本项目包含一个基于 Docker Compose 的完整服务栈（后端、Python 服务、nginx、MySQL 等）。此说明面向非 Docker 专业评审，步骤简单明了，方便快速验证与部署。

## 1. 环境要求

- 操作系统：Linux / macOS / Windows（WSL2 推荐）
- Docker：建议使用 Docker 20.x 以上
- Docker Compose：建议使用 Compose V2（随 Docker Desktop 或 Docker Engine 安装），确认命令为 `docker compose`（而不是 `docker-compose`）。

## 2. 评审说明

内置 Key：为确保评审顺利，本项目在 .env 文件中已内置了 测试专用 API Key（包含少量余额）。

开箱即用：评委无需自行申请阿里云或 LangSmith 账号，解压并运行 docker-compose up 即可直接体验完整 AI 功能。

安全性：相关 Key 仅供本次 4C 比赛评审使用，项目结束后将自动失效

## 3. 一键启动

**注意**：操作前请在项目根目录（包含 `docker-compose.yml`）执行下列命令。
在项目根运行：

```

docker compose up -d

```

此命令会：

- 构建或拉取镜像（若 `docker-compose.yml` 指定 `build:`，将会本地构建）
- 启动所有服务并在后台运行

查看日志（实时）：

```

docker compose logs -f

```

停止并移除服务：

```

docker compose down

```

---

## 4. 访问方式

- 前端（通过 nginx）：打开浏览器访问 `https://localhost`（HTTPS 使用 443 端口）

评审请优先在浏览器访问：

```

https://localhost

```

---

## 5. 常见问题与解决

- Q: `The "LANGCHAIN_ENDPOINT" variable is not set.` 警告怎么办？
    - A: 在 `.env` 中添加对应变量或在 shell 中导出。例如：
        ```bash
        export LANGCHAIN_ENDPOINT=https://eu.api.smith.langchain.com
        ```

- Q: `docker compose images` 报 `No such image: sha256:...` 或构建失败
    - A: 执行一次清理并重建：
        ```bash
        docker compose down --rmi local
        docker compose build --parallel
        docker compose up -d
        ```
        注意：`--rmi local` 会删除由 compose 构建的本地镜像，不会删除来自 registry 的官方镜像。

- Q: 端口被占用（比如 80、443、8000、8081、3306）怎么办？
    - A: 有两种方式：
        1. 停止占用端口的进程（在 Linux 上查看：`sudo lsof -i :80` / `sudo ss -ltnp | grep 80`），然后停止或调整该服务。
        2. 修改 `docker-compose.yml` 中对应服务的映射端口，例如把 `80:80` 改为 `8088:80`（宿主机端口改为 8088）。修改后重新执行 `docker compose up -d`。

- Q: 我想离线分发镜像（不使用 registry），如何导出？
    - A: 在构建完成后，用 `docker save` 导出需要的镜像为 `.tar`，在目标机用 `docker load` 导入。示例：
        ```bash
        docker save -o stack-images.tar <image1:tag> <image2:tag>
        # 在目标机
        docker load -i stack-images.tar
        docker compose up -d
        ```

---

```

```
