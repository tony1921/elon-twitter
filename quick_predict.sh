#!/bin/bash
# 快速预测脚本 - 直接输入推文数量进行预测

if [ -z "$1" ]; then
    echo "用法: ./quick_predict.sh <推文数量>"
    echo "示例: ./quick_predict.sh 100"
    echo ""
    echo "提示：访问 https://xtracker.polymarket.com 查看当前推文数量"
    exit 1
fi

echo "$1" | python3 elon_predictor_enhanced.py <<EOF
2
1
EOF
