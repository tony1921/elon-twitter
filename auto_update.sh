#!/bin/bash
# 完整自动更新 - 每小时更新数据、Excel、看板并推送Telegram

echo "============================================================"
echo "  🔄 Elon Musk 推文数据 - 完整自动更新系统"
echo "============================================================"
echo "每 5 分钟自动执行:"
echo "  ✅ 获取最新推文数据"
echo "  ✅ 更新Excel表格"
echo "  ✅ 更新Web看板"
echo "  ✅ 推送Telegram通知"
echo ""
echo "按 Ctrl+C 停止"
echo "============================================================"
echo ""

INTERVAL=300  # 5分钟

while true; do
    echo "[$(date '+%H:%M:%S')] 开始自动更新..."
    echo ""

    python3 update_dashboard.py

    echo ""
    echo "⏰ 下次更新: $(date -v+5M '+%H:%M')"
    echo "============================================================"
    echo ""

    sleep $INTERVAL
done
