#!/bin/bash
# Elon Musk Tweet 预测系统 - 快速启动脚本

echo "╔══════════════════════════════════════════════════════════════╗"
echo "║                                                                ║"
echo "║        🤖 Elon Musk 推文预测系统 - 启动中                     ║"
echo "║                                                                ║"
echo "╚══════════════════════════════════════════════════════════════╝"
echo ""

# 检查 Python
if ! command -v python3 &> /dev/null; then
    echo "❌ 错误: 未找到 Python3"
    echo "请先安装 Python: https://www.python.org/downloads/"
    exit 1
fi

echo "✓ Python3 已安装"

# 检查依赖
echo ""
echo "检查依赖..."

python3 -c "import requests" 2>/dev/null || {
    echo "❌ 缺少依赖库，正在安装..."
    pip3 install requests beautifulsoup4 numpy scipy pytz
}

echo "✓ 所有依赖已就绪"

# 启动程序
echo ""
echo "🚀 启动预测系统..."
echo ""

python3 elon_predictor_enhanced.py
