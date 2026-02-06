#!/usr/bin/env python3
"""
处理历史数据，生成每日统计
"""

import json
from datetime import datetime
from collections import OrderedDict

def process_historical_data():
    """处理历史数据"""

    print("=" * 70)
    print("  📊 处理历史数据")
    print("=" * 70)

    # 读取原始数据
    with open('data/raw_historical.json', 'r') as f:
        raw_data = json.load(f)

    if not raw_data.get('data'):
        print("❌ 无数据")
        return

    posts = raw_data['data']
    print(f"\n📝 总推文数: {len(posts)}")

    # 按日期统计
    daily_counts = OrderedDict()
    daily_details = {}

    for post in posts:
        created_at = post.get('createdAt', '')
        if created_at:
            date = created_at.split('T')[0]
            daily_counts[date] = daily_counts.get(date, 0) + 1

            # 保存详情
            if date not in daily_details:
                daily_details[date] = []
            daily_details[date].append({
                'id': post.get('platformId'),
                'time': created_at.split('T')[1][:5],
                'content': post.get('content', '')[:50]
            })

    # 按日期排序
    daily_counts = OrderedDict(sorted(daily_counts.items()))

    print(f"📅 天数: {len(daily_counts)}")
    print(f"📅 最早: {list(daily_counts.keys())[0]}")
    print(f"📅 最晚: {list(daily_counts.keys())[-1]}")

    # 生成每日记录格式
    daily_records = []
    for date, count in daily_counts.items():
        record = {
            "date": date,
            "count": count,
            "source": "xtracker_historical",
            "details_count": len(daily_details.get(date, [])),
            "created_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        }
        daily_records.append(record)

    # 保存每日数据
    with open('data/daily_tweets.json', 'w') as f:
        json.dump(daily_records, f, ensure_ascii=False, indent=2)

    print(f"\n✅ 每日数据已保存到: data/daily_tweets.json")

    # 显示统计
    print(f"\n📊 每日推文统计 (最近10天):")
    print("=" * 70)

    for record in daily_records[-10:]:
        date = record['date']
        count = record['count']
        print(f"  {date}: {count:3d} 条")

    # 总体统计
    counts = [r['count'] for r in daily_records]
    print(f"\n📈 总体统计:")
    print(f"  平均: {sum(counts) / len(counts):.1f} 条/天")
    print(f"  最高: {max(counts)} 条")
    print(f"  最低: {min(counts)} 条")
    print(f"  总计: {sum(counts)} 条")

    # 查找最高和最低的日期
    max_date = max(daily_counts, key=daily_counts.get)
    min_date = min(daily_counts, key=daily_counts.get)
    print(f"  最多: {max_date} ({daily_counts[max_date]} 条)")
    print(f"  最少: {min_date} ({daily_counts[min_date]} 条)")

    print("=" * 70)

    return daily_records


if __name__ == "__main__":
    process_historical_data()
