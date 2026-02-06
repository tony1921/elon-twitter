#!/bin/bash
# 启动Web看板服务器

PORT=8888

echo "============================================================"
echo "  🌐 启动Web看板"
echo "============================================================"
echo ""
echo "看板地址: http://localhost:$PORT"
echo "按 Ctrl+C 停止服务器"
echo ""
echo "============================================================"

# 尝试使用Python 3启动HTTP服务器
cd /Users/tony777/polymarket-predictor

if command -v python3 &> /dev/null; then
    python3 -m http.server $PORT
else
    echo "❌ 未找到 Python3"
    exit 1
fi
