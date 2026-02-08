#!/usr/bin/env python3
"""
添加 Polymarket 市场数据到看板
支持多个市场的追踪
"""

import json
import requests
from datetime import datetime, timedelta

# Polymarket 市场定义
POLYMARKET_MARKETS = [
    {
        'name': 'Feb 7 - Feb 9, 2026',
        'title': 'Feb 7-9 Market',
        'start_et': '2026-02-07T12:00:00',
        'end_et': '2026-02-09T12:00:00',
        'start_utc': '2026-02-07T17:00:00.000Z',
        'end_utc': '2026-02-09T17:00:00.000Z'
    },
    {
        'name': 'Feb 3 - Feb 10, 2026',
        'title': 'Feb 3-10 Market',
        'start_et': '2026-02-03T12:00:00',
        'end_et': '2026-02-10T12:00:00',
        'start_utc': '2026-02-03T17:00:00.000Z',
        'end_utc': '2026-02-10T17:00:00.000Z'
    }
]

def fetch_market_data(start_utc, end_utc):
    """从API获取指定时间范围的推文数据"""
    url = 'https://xtracker.polymarket.com/api/users/elonmusk/posts'

    try:
        response = requests.get(
            url,
            params={
                'startDate': start_utc,
                'endDate': end_utc
            },
            headers={'User-Agent': 'Mozilla/5.0'},
            timeout=30
        )

        if response.status_code == 200:
            data = response.json()
            if data.get('data'):
                posts = data['data']

                # 按EST时区分组统计
                daily_counts = {}
                for post in posts:
                    created_at = post.get('createdAt', '')
                    if created_at:
                        dt = datetime.fromisoformat(created_at.replace('Z', '+00:00'))
                        est_dt = dt - timedelta(hours=5)
                        date = est_dt.strftime("%Y-%m-%d")
                        daily_counts[date] = daily_counts.get(date, 0) + 1

                return {
                    'total': len(posts),
                    'daily': daily_counts
                }

    except Exception as e:
        print(f"❌ 获取数据失败: {e}")

    return None


def update_dashboard_with_markets():
    """更新看板数据，包含所有市场"""

    # 加载现有看板数据
    try:
        with open('data/dashboard_data.json', 'r') as f:
            dashboard_data = json.load(f)
    except:
        dashboard_data = {}

    # 添加市场数据
    markets_data = []

    for market in POLYMARKET_MARKETS:
        print(f"\n📊 获取市场: {market['name']}")
        print(f"   时间范围: {market['start_et']} ET - {market['end_et']} ET")

        data = fetch_market_data(market['start_utc'], market['end_utc'])

        if data:
            market_info = {
                'name': market['name'],
                'title': market['title'],
                'total': data['total'],
                'daily': data['daily'],
                'start_et': market['start_et'],
                'end_et': market['end_et']
            }

            # 计算每日平均
            days = len(data['daily'])
            if days > 0:
                market_info['avg'] = data['total'] / days

            markets_data.append(market_info)

            print(f"   总计: {data['total']} 条")

            for date, count in sorted(data['daily'].items()):
                print(f"     {date}: {count} 条")
        else:
            print(f"   ⚠️  获取失败")

    # 更新看板数据
    dashboard_data['polymarket_markets'] = markets_data
    dashboard_data['last_update'] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    # 保存
    with open('data/dashboard_data.json', 'w') as f:
        json.dump(dashboard_data, f, ensure_ascii=False, indent=2)

    print(f"\n✅ 看板数据已更新")
    print(f"   共 {len(markets_data)} 个市场")

    return dashboard_data


if __name__ == "__main__":
    print("=" * 70)
    print("  📊 添加 Polymarket 市场数据")
    print("=" * 70)

    update_dashboard_with_markets()

    print("=" * 70)
