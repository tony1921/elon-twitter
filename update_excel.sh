#!/bin/bash
# 快捷更新Excel表格

echo "🔄 更新Excel表格..."
python3 generate_excel.py

echo ""
echo "✅ 完成！"
echo "📂 文件位置: data/elon_musk_tweets.xlsx"
echo ""
echo "💡 提示: 可以用以下命令打开:"
echo "   open data/elon_musk_tweets.xlsx"
