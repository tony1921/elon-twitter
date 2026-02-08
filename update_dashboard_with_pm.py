#!/usr/bin/env python3
"""
更新看板数据 - 使用 Polymarket 时间范围
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

# 当前追踪期间配置（完整日历日期）
CURRENT_PERIOD = {
    'name': 'Feb 1 - Feb 28, 2026',
    'start': '2026-02-01T00:00:00.000Z',
    'end': '2026-02-28T23:59:59.000Z'
}

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


def update_dashboard_data():
    """更新看板数据"""

    # 加载历史数据（完整日历日期）
    try:
        with open('data/daily_tweets.json', 'r') as f:
            full_calendar_data = json.load(f)
    except:
        full_calendar_data = []

    # 获取 Polymarket 市场数据
    markets_data = []
    primary_market_data = None  # 主要市场（Feb 3-10）

    for market in POLYMARKET_MARKETS:
        print(f"📊 获取市场: {market['name']}")

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

            # 保存 Feb 3-10 市场作为主要数据源
            if 'Feb 3' in market['name']:
                primary_market_data = market_info

    # 生成看板数据
    today_str = datetime.now().strftime("%Y-%m-%d")

    # 使用完整日历数据获取今日数据
    today_record = None
    for record in full_calendar_data:
        if record['date'] == today_str:
            today_record = record
            break

    if not today_record:
        today_record = {'count': 0}

    # 计算统计数据（基于完整日历数据）
    sorted_data = sorted(full_calendar_data, key=lambda x: x['date'])
    counts = [r['count'] for r in sorted_data]
    recent_7 = sorted_data[-7:]

    # 使用 Polymarket 市场数据作为"最近7天"
    polymarket_recent_days = []
    if primary_market_data:
        for date, count in sorted(primary_market_data['daily'].items()):
            polymarket_recent_days.append({
                'date': date,
                'count': count
            })

    dashboard_data = {
        'last_update': datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        'today': {
            'date': today_str,
            'count': today_record['count'],
            'vs_avg': today_record['count'] - (sum(counts) / len(counts)) if counts else 0
        },
        'week_avg': sum([r['count'] for r in recent_7]) / len(recent_7) if recent_7 else 0,
        'stats': {
            'total_days': len(sorted_data),
            'avg': sum(counts) / len(counts) if counts else 0,
            'max': max(counts) if counts else 0,
            'min': min(counts) if counts else 0,
            'max_date': max(sorted_data, key=lambda x: x['count'])['date'] if sorted_data else ''
        },
        # 使用完整日历数据的最近7天
        'recent_days': [
            {
                'date': r['date'],
                'count': r['count']
            }
            for r in recent_7
        ],
        # 使用 Polymarket 市场数据
        'polymarket_recent_days': polymarket_recent_days,
        'polymarket_markets': markets_data
    }

    # 保存看板数据
    with open('data/dashboard_data.json', 'w') as f:
        json.dump(dashboard_data, f, ensure_ascii=False, indent=2)

    print(f"\n✅ 看板数据已更新")
    print(f"   Polymarket 最近7天: {len(polymarket_recent_days)} 天")

    return dashboard_data


def main():
    """主函数"""

    print("=" * 70)
    print("  🔄 更新数据 (Polymarket 时间范围)")
    print("=" * 70)

    try:
        dashboard_data = update_dashboard_data()

        if dashboard_data.get('polymarket_recent_days'):
            print("\n📊 Polymarket 最近几天:")
            total = 0
            for day in dashboard_data['polymarket_recent_days']:
                print(f"   {day['date']}: {day['count']} 条")
                total += day['count']
            print(f"   总计: {total} 条")

        print("\n✅ 全部完成！")
    except Exception as e:
        print(f"\n❌ 更新失败: {e}")
        import traceback
        traceback.print_exc()

    print("=" * 70)


if __name__ == "__main__":
    main()
