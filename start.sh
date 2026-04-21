#!/bin/bash

# 遇到错误立即退出
set -e

echo "=========================================="
echo "   🚀 一键构建并启动全部服务 (Production) "
echo "=========================================="

# 1. 检查 Docker 环境
if ! command -v docker &> /dev/null; then
    echo "❌ 错误: Docker 未安装，请先安装 Docker。"
    exit 1
fi

# 2. 兼容性检查：确定使用 'docker compose' 还是 'docker-compose'
if docker compose version &> /dev/null; then
    DOCKER_CMD="docker compose"
elif command -v docker-compose &> /dev/null; then
    DOCKER_CMD="docker-compose"
else
    echo "❌ 错误: 未检测到 docker compose 插件或命令。"
    exit 1
fi

echo -e "\n[1/2] 🛠️  开始构建所有服务 (含国内镜像优化)..."
# 使用 --pull 确保基础镜像也是最新的
$DOCKER_CMD build --pull

echo -e "\n[2/2] 🌐 启动所有服务 (后台运行)..."
$DOCKER_CMD up -d

echo "------------------------------------------"
echo "✅ 所有服务已成功构建并启动！"
echo "📊 当前服务状态："
$DOCKER_CMD ps
echo "------------------------------------------"
echo "💡 提示: 使用 '$DOCKER_CMD logs -f' 查看实时日志"