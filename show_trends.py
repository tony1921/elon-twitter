#!/usr/bin/env python3
"""
查看推文趋势和预测
"""

import json
import os
from datetime import datetime

DATA_FILE = "data/daily_tweets.json"


def load_data():
    if os.path.exists(DATA_FILE):
        with open(DATA_FILE, 'r', encoding='utf-8') as f:
            return json.load(f)
    return []


def show_trends():
    data = load_data()

    if not data:
        print("📭 暂无数据")
        return

    # 按日期排序
    sorted_data = sorted(data, key=lambda x: x['date'])

    print("\n" + "=" * 70)
    print("  📈 Elon Musk 推文趋势")
    print("=" * 70)

    # 显示所有记录
    print("\n📊 历史记录:")
    for record in sorted_data:
        print(f"  {record['date']}: {record['count']} 条")

    # 统计信息
    counts = [r['count'] for r in sorted_data]
    days = len(counts)

    print(f"\n📈 统计 (共 {days} 天):")
    print(f"  平均: {sum(counts) / days:.1f} 条/天")
    print(f"  最高: {max(counts)} 条")
    print(f"  最低: {min(counts)} 条")

    # 趋势分析
    if days >= 3:
        recent_3 = counts[-3:]
        previous_3 = counts[-6:-3] if days >= 6 else counts[:-3]

        if previous_3:
            avg_recent = sum(recent_3) / 3
            avg_previous = sum(previous_3) / len(previous_3)

            print(f"\n📉 趋势分析:")
            print(f"  最近3天: {avg_recent:.1f} 条/天")
            print(f"  前3天: {avg_previous:.1f} 条/天")

            change = ((avg_recent - avg_previous) / avg_previous) * 100
            if change > 10:
                print(f"  趋势: 上升 ↗️ (+{change:.1f}%)")
            elif change < -10:
                print(f"  趋势: 下降 ↘️ ({change:.1f}%)")
            else:
                print(f"  趋势: 稳定 ➡️ ({change:+.1f}%)")

    # 预测
    if days >= 3:
        # 使用加权平均，最近的天权重更高
        weights = [3, 2, 1]
        recent = counts[-3:]
        weighted_avg = sum(r * w for r, w in zip(recent, weights)) / sum(weights)

        print(f"\n🔮 明天预测: 约 {int(weighted_avg)} 条")

        # 简单的范围预测
        std = (max(counts) - min(counts)) / 4  # 粗略估计标准差
        low = int(weighted_avg - std)
        high = int(weighted_avg + std)
        print(f"  预测范围: {low} - {high} 条")

    print("=" * 70)


if __name__ == "__main__":
    show_trends()
